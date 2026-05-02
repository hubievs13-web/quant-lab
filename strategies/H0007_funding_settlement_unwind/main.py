# H0007_funding_settlement_unwind
#
# QuantConnect Lean v17685 assumption:
# - Binance USD-M perpetual futures are accessed with add_crypto_future("BTCUSDT"/"ETHUSDT",
#   Resolution.MINUTE, Market.BINANCE).
# - If this symbol mapping or brokerage model is not supported in project 30774195,
#   stop after the smoke test and treat the strategy as technically blocked until fixed.
#
# Friction model:
# - Custom taker fee model charges 0.04% per side.
# - Custom slippage model applies 0.05% per side.
# - Expected round-trip friction is therefore about 0.08% fees + 0.10% slippage = 0.18%.

from AlgorithmImports import *
from collections import deque
from datetime import timedelta
import math


# Exactly three H0007 free parameters.
PRE_SETTLEMENT_WINDOW_MINUTES = 30
DISPLACEMENT_PCT = 0.35
HOLD_BARS = 3


# Fixed implementation/risk constants, not hypothesis tuning knobs.
TAKER_FEE_RATE = 0.0004
SLIPPAGE_RATE_PER_SIDE = 0.0005
MAX_SESSION_DRAWDOWN = 0.20
STARTING_CASH_USDT = 200
LEVERAGE = 2.0
MARGIN_FRACTION_PER_SYMBOL = 0.45
BAR_MINUTES = 5


class BinanceFuturesTakerFeeModel(FeeModel):
    def get_order_fee(self, parameters):
        security = parameters.security
        order = parameters.order
        price = security.price
        if price <= 0:
            price = order.price
        fee = abs(float(order.absolute_quantity) * float(price) * TAKER_FEE_RATE)
        return OrderFee(CashAmount(fee, "USDT"))


class ConstantPercentSlippageModel:
    def get_slippage_approximation(self, asset, order):
        return asset.price * SLIPPAGE_RATE_PER_SIDE


class SymbolState:
    def __init__(self, symbol, ticker):
        self.symbol = symbol
        self.ticker = ticker
        self.recent_bars = deque(maxlen=256)
        self.closes_by_end_time = {}
        self.pending_entry = None
        self.pending_exit = False
        self.entry_order_id = None
        self.exit_order_id = None
        self.position_open = False
        self.entry_time = None
        self.entry_price = 0.0
        self.entry_quantity = 0.0
        self.entry_fee = 0.0
        self.entry_signal_time = None
        self.entry_side = ""
        self.bars_held = 0
        self.current_trade = None


class FundingSettlementUnwind(QCAlgorithm):
    def initialize(self):
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2025, 1, 1)
        self.set_account_currency("USDT", STARTING_CASH_USDT)

        # Brokerage enum support for Binance USD-M Futures can vary by Lean version.
        # The README contains the required smoke-test verification step.
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)

        self.states = {}
        self.order_id_to_context = {}
        self.active_submission_context = None
        self.day_stats = self._new_day_stats()
        self.current_day = None
        self.session_peak = STARTING_CASH_USDT
        self.session_stop = False

        for ticker in ["BTCUSDT", "ETHUSDT"]:
            security = self.add_crypto_future(
                ticker,
                Resolution.MINUTE,
                market=Market.BINANCE,
                fill_forward=False,
                leverage=LEVERAGE,
            )
            symbol = security.symbol
            self.states[symbol] = SymbolState(symbol, ticker)

            self.securities[symbol].set_fee_model(BinanceFuturesTakerFeeModel())
            self.securities[symbol].set_slippage_model(ConstantPercentSlippageModel())
            self.securities[symbol].set_leverage(LEVERAGE)

            consolidator = TradeBarConsolidator(timedelta(minutes=BAR_MINUTES))
            consolidator.data_consolidated += self.on_five_minute_bar
            self.subscription_manager.add_consolidator(symbol, consolidator)

            self.debug(
                "SYMBOL_MAPPING "
                f"ticker={ticker} symbol={symbol} "
                f"security_type={self.securities[symbol].type} "
                f"market={self.securities[symbol].symbol.id.market}"
            )

        self.debug(
            "INIT H0007 params "
            f"pre_settlement_window_minutes={PRE_SETTLEMENT_WINDOW_MINUTES} "
            f"displacement_pct={DISPLACEMENT_PCT} hold_bars={HOLD_BARS} "
            f"fee_per_side={TAKER_FEE_RATE:.4%} slippage_per_side={SLIPPAGE_RATE_PER_SIDE:.4%}"
        )

    def on_data(self, slice):
        self._handle_day_rollover()
        self._update_session_drawdown()
        self._reconcile_portfolio_state()
        self._execute_pending_orders(slice)

    def on_five_minute_bar(self, sender, bar):
        state = self.states.get(bar.symbol)
        if state is None:
            return

        bar_end = bar.end_time
        state.recent_bars.append(bar)
        state.closes_by_end_time[bar_end] = float(bar.close)

        cutoff = bar_end - timedelta(days=2)
        old_keys = [time for time in state.closes_by_end_time if time < cutoff]
        for key in old_keys:
            del state.closes_by_end_time[key]

        if state.position_open and state.entry_time is not None and bar_end > state.entry_time:
            state.bars_held += 1
            if state.bars_held >= HOLD_BARS and not state.pending_exit:
                state.pending_exit = True

        self._create_settlement_signal(state, bar)

    def on_order_event(self, order_event):
        context = self.order_id_to_context.get(order_event.order_id)
        if context is None:
            context = self._context_from_active_submission(order_event)
        if context is None:
            context = self._context_from_state(order_event)
        if context is None:
            self.debug(
                "ORDER_EVENT_UNMATCHED "
                f"timestamp={self.time} order_id={order_event.order_id} "
                f"symbol={order_event.symbol} status={order_event.status} "
                f"message={order_event.message}"
            )
            return

        state = self.states[context["symbol"]]
        if order_event.status == OrderStatus.INVALID or order_event.status == OrderStatus.CANCELED:
            self.debug(
                "ORDER_ERROR "
                f"timestamp={self.time} symbol={state.ticker} order_id={order_event.order_id} "
                f"status={order_event.status} message={order_event.message}"
            )
            if context["type"] == "entry":
                state.entry_order_id = None
                state.pending_entry = None
            if context["type"] == "exit":
                state.exit_order_id = None
                state.pending_exit = False
            return

        fill_price = float(order_event.fill_price)
        fill_qty = float(order_event.fill_quantity)
        if order_event.status != OrderStatus.FILLED and abs(fill_qty) <= 0:
            return

        fee = abs(fill_price * fill_qty * TAKER_FEE_RATE)

        if context["type"] == "entry":
            self._mark_entry_filled(state, context, fill_price, fill_qty, fee, self.time, "ORDER_EVENT")
            return

        if context["type"] == "exit" and state.current_trade is not None:
            self._mark_exit_filled(state, context, fill_price, fee, self.time)

    def on_end_of_algorithm(self):
        self._flatten_open_positions("END_OF_ALGORITHM_FLATTEN")
        self._log_daily_summary(force=True)

    def _create_settlement_signal(self, state, bar):
        bar_end = bar.end_time
        settlement_time = bar_end - timedelta(minutes=BAR_MINUTES)

        if settlement_time.minute != 0 or settlement_time.second != 0:
            return
        if settlement_time.hour not in [0, 8, 16]:
            return
        if state.position_open or state.pending_entry is not None:
            return

        start_time = settlement_time - timedelta(minutes=PRE_SETTLEMENT_WINDOW_MINUTES)
        last_pre_settlement_time = settlement_time - timedelta(minutes=BAR_MINUTES)

        if start_time not in state.closes_by_end_time:
            self.debug(
                f"DATA_GAP timestamp={self.time} symbol={state.ticker} "
                f"missing_pre_window_start={start_time}"
            )
            return
        if last_pre_settlement_time not in state.closes_by_end_time:
            self.debug(
                f"DATA_GAP timestamp={self.time} symbol={state.ticker} "
                f"missing_last_pre_settlement={last_pre_settlement_time}"
            )
            return

        start_close = state.closes_by_end_time[start_time]
        last_close = state.closes_by_end_time[last_pre_settlement_time]
        if start_close <= 0:
            return

        displacement = 100.0 * (last_close / start_close - 1.0)
        side = ""
        quantity_sign = 0
        if displacement >= DISPLACEMENT_PCT:
            side = "short"
            quantity_sign = -1
        elif displacement <= -DISPLACEMENT_PCT:
            side = "long"
            quantity_sign = 1
        else:
            return

        state.pending_entry = {
            "side": side,
            "quantity_sign": quantity_sign,
            "signal_time": bar_end,
            "settlement_time": settlement_time,
            "displacement_pct": displacement,
        }
        self.debug(
            "SIGNAL "
            f"timestamp={self.time} symbol={state.ticker} side={side} "
            f"settlement_time={settlement_time} signal_bar_time={bar_end} "
            f"pre_window_start={start_time} last_pre_settlement={last_pre_settlement_time} "
            f"displacement_pct={displacement:.5f}"
        )

    def _execute_pending_orders(self, slice):
        if self.session_stop:
            return

        for symbol, state in self.states.items():
            if state.pending_exit and state.position_open:
                if state.exit_order_id is not None:
                    continue
                if self.time <= state.entry_time:
                    continue
                quantity = -self.portfolio[symbol].quantity
                if quantity != 0:
                    context = {
                        "type": "exit",
                        "symbol": symbol,
                        "reason_code": "TIME_EXIT",
                    }
                    self.active_submission_context = context
                    ticket = self.market_order(symbol, quantity, tag="H0007_TIME_EXIT")
                    self.order_id_to_context[ticket.order_id] = context
                    if state.position_open:
                        state.exit_order_id = ticket.order_id
                    self.active_submission_context = None
                    self.debug(
                        "EXIT_ORDER_SUBMITTED "
                        f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                        f"quantity={quantity} reason_code=TIME_EXIT "
                        f"entry_time={state.entry_time} holding_bars={state.bars_held}"
                    )
                    self._reconcile_portfolio_state()
                continue

            if state.pending_entry is None or state.position_open:
                continue
            if state.entry_order_id is not None:
                continue
            if self.time <= state.pending_entry["signal_time"]:
                continue
            if symbol not in slice.bars:
                continue

            price = self.securities[symbol].price
            quantity = self._position_quantity(symbol, price, state.pending_entry["quantity_sign"])
            if quantity == 0:
                self.debug(
                    f"ORDER_SKIPPED_ZERO_QTY timestamp={self.time} symbol={state.ticker} price={price:.8f}"
                )
                state.pending_entry = None
                continue

            context = {
                "type": "entry",
                "symbol": symbol,
                "side": state.pending_entry["side"],
                "signal_time": state.pending_entry["signal_time"],
                "quantity": quantity,
            }
            self.active_submission_context = context
            ticket = self.market_order(symbol, quantity, tag="H0007_ENTRY")
            self.order_id_to_context[ticket.order_id] = context
            if not state.position_open:
                state.entry_order_id = ticket.order_id
            self.active_submission_context = None
            self.debug(
                "ENTRY_ORDER_SUBMITTED "
                f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                f"side={context['side']} quantity={quantity} "
                f"signal_bar_time={context['signal_time']} planned_execution_time={self.time}"
            )
            self._reconcile_portfolio_state()

    def _position_quantity(self, symbol, price, quantity_sign):
        if price <= 0:
            return 0

        notional = self.portfolio.total_portfolio_value * MARGIN_FRACTION_PER_SYMBOL * LEVERAGE
        raw_quantity = notional / price
        lot_size = float(self.securities[symbol].symbol_properties.lot_size)
        if lot_size <= 0:
            lot_size = 0.001
        rounded_quantity = math.floor(raw_quantity / lot_size) * lot_size
        if rounded_quantity <= 0:
            return 0
        return quantity_sign * rounded_quantity

    def _update_session_drawdown(self):
        equity = self.portfolio.total_portfolio_value
        if equity > self.session_peak:
            self.session_peak = equity

        drawdown = 0.0
        if self.session_peak > 0:
            drawdown = (self.session_peak - equity) / self.session_peak
        if drawdown > self.day_stats["max_intraday_drawdown"]:
            self.day_stats["max_intraday_drawdown"] = drawdown

        if drawdown >= MAX_SESSION_DRAWDOWN and not self.session_stop:
            self.session_stop = True
            self.debug(
                f"SESSION_STOP timestamp={self.time} drawdown_pct={drawdown * 100.0:.2f} "
                f"threshold_pct={MAX_SESSION_DRAWDOWN * 100.0:.2f}"
            )
            for symbol, state in self.states.items():
                state.pending_entry = None
                if self.portfolio[symbol].invested:
                    quantity = -self.portfolio[symbol].quantity
                    if quantity != 0 and state.exit_order_id is None:
                        context = {
                            "type": "exit",
                            "symbol": symbol,
                            "reason_code": "SESSION_DRAWDOWN_STOP",
                        }
                        self.active_submission_context = context
                        ticket = self.market_order(symbol, quantity, tag="H0007_SESSION_DRAWDOWN_STOP")
                        self.order_id_to_context[ticket.order_id] = context
                        if state.position_open:
                            state.exit_order_id = ticket.order_id
                        self.active_submission_context = None
                        self.debug(
                            "EXIT_ORDER_SUBMITTED "
                            f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                            f"quantity={quantity} reason_code=SESSION_DRAWDOWN_STOP "
                            f"entry_time={state.entry_time} holding_bars={state.bars_held}"
                        )

    def _handle_day_rollover(self):
        today = self.time.date()
        if self.current_day is None:
            self.current_day = today
            self.session_peak = self.portfolio.total_portfolio_value
            return
        if today == self.current_day:
            return

        self._log_daily_summary(force=True)
        self.current_day = today
        self.day_stats = self._new_day_stats()
        self.session_peak = self.portfolio.total_portfolio_value
        self.session_stop = False

    def _log_daily_summary(self, force=False):
        if self.current_day is None:
            return
        trades = self.day_stats["trade_count"]
        if trades == 0 and not force:
            return

        win_rate = 0.0
        avg_pre_fee = 0.0
        avg_post_fee = 0.0
        if trades > 0:
            win_rate = 100.0 * self.day_stats["wins"] / trades
            avg_pre_fee = self.day_stats["pre_fee_sum"] / trades
            avg_post_fee = self.day_stats["post_fee_sum"] / trades

        self.debug(
            "DAILY_SUMMARY "
            f"date={self.current_day} trade_count={trades} win_rate_pct={win_rate:.2f} "
            f"avg_pre_fee_edge_pct={avg_pre_fee:.5f} avg_post_fee_edge_pct={avg_post_fee:.5f} "
            f"max_intraday_drawdown_pct={self.day_stats['max_intraday_drawdown'] * 100.0:.2f}"
        )

    def _new_day_stats(self):
        return {
            "trade_count": 0,
            "wins": 0,
            "pre_fee_sum": 0.0,
            "post_fee_sum": 0.0,
            "max_intraday_drawdown": 0.0,
        }

    def _context_from_active_submission(self, order_event):
        context = self.active_submission_context
        if context is None:
            return None
        if order_event.symbol != context["symbol"]:
            return None
        return context

    def _context_from_state(self, order_event):
        for symbol, state in self.states.items():
            if order_event.symbol != symbol:
                continue
            if state.entry_order_id == order_event.order_id:
                if state.current_trade is not None:
                    return None
                if state.pending_entry is not None:
                    return {
                        "type": "entry",
                        "symbol": symbol,
                        "side": state.pending_entry["side"],
                        "signal_time": state.pending_entry["signal_time"],
                        "quantity": self.portfolio[symbol].quantity,
                    }
            if state.exit_order_id == order_event.order_id:
                return {
                    "type": "exit",
                    "symbol": symbol,
                    "reason_code": "TIME_EXIT",
                }
        return None

    def _mark_entry_filled(self, state, context, fill_price, fill_qty, fee, fill_time, source):
        if state.current_trade is not None:
            return

        state.position_open = True
        state.entry_time = fill_time
        state.entry_price = fill_price
        state.entry_quantity = fill_qty
        state.entry_fee = fee
        state.entry_signal_time = context["signal_time"]
        state.entry_side = context["side"]
        state.bars_held = 0
        state.pending_entry = None
        state.entry_order_id = None
        state.current_trade = {
            "side": context["side"],
            "signal_time": context["signal_time"],
            "execution_time": fill_time,
            "entry_price": fill_price,
            "entry_quantity": fill_qty,
            "entry_fee": fee,
        }
        delta_minutes = (fill_time - context["signal_time"]).total_seconds() / 60.0
        self.debug(
            "ENTRY "
            f"timestamp={fill_time} symbol={state.ticker} side={context['side']} "
            f"signal_bar_time={context['signal_time']} execution_bar_time={fill_time} "
            f"delta_minutes={delta_minutes:.1f} entry_price={fill_price:.8f} "
            f"source={source}"
        )

    def _mark_exit_filled(self, state, context, fill_price, fee, fill_time):
        if state.current_trade is None:
            return

        trade = state.current_trade
        side = trade["side"]
        qty = float(trade["entry_quantity"])
        entry_price = float(trade["entry_price"])
        direction = 1.0 if side == "long" else -1.0
        gross_pnl = (fill_price - entry_price) * abs(qty) * direction
        notional = abs(entry_price * qty)
        pre_fee_pct = 0.0
        post_fee_pct = 0.0
        if notional > 0:
            pre_fee_pct = 100.0 * gross_pnl / notional
            post_fee_pct = 100.0 * (gross_pnl - trade["entry_fee"] - fee) / notional

        is_win = post_fee_pct > 0
        self.day_stats["trade_count"] += 1
        self.day_stats["wins"] += 1 if is_win else 0
        self.day_stats["pre_fee_sum"] += pre_fee_pct
        self.day_stats["post_fee_sum"] += post_fee_pct

        delta_minutes = (trade["execution_time"] - trade["signal_time"]).total_seconds() / 60.0
        self.debug(
            "TRADE "
            f"timestamp={fill_time} symbol={state.ticker} side={side} "
            f"signal_bar_time={trade['signal_time']} execution_bar_time={trade['execution_time']} "
            f"delta_minutes={delta_minutes:.1f} entry_price={entry_price:.8f} "
            f"exit_price={fill_price:.8f} holding_bars={state.bars_held} "
            f"reason_code={context['reason_code']} pre_fee_pnl_pct={pre_fee_pct:.5f} "
            f"post_fee_pnl_pct={post_fee_pct:.5f}"
        )
        self._clear_position_state(state)

    def _clear_position_state(self, state):
        state.position_open = False
        state.entry_time = None
        state.entry_price = 0.0
        state.entry_quantity = 0.0
        state.entry_fee = 0.0
        state.entry_signal_time = None
        state.entry_side = ""
        state.bars_held = 0
        state.pending_exit = False
        state.entry_order_id = None
        state.exit_order_id = None
        state.current_trade = None

    def _reconcile_portfolio_state(self):
        for symbol, state in self.states.items():
            holding = self.portfolio[symbol]
            if holding.invested and not state.position_open:
                self.debug(
                    "STATE_DESYNC "
                    f"timestamp={self.time} symbol={state.ticker} "
                    "portfolio_invested=True state_position_open=False action=recover_entry"
                )
                self._recover_entry_from_holding(state, "STATE_RECONCILE")
            elif not holding.invested and state.position_open and state.current_trade is not None:
                self.debug(
                    "STATE_DESYNC "
                    f"timestamp={self.time} symbol={state.ticker} "
                    "portfolio_invested=False state_position_open=True action=clear_state"
                )
                context = {
                    "type": "exit",
                    "symbol": symbol,
                    "reason_code": "STATE_DESYNC_FLATTEN",
                }
                self._mark_exit_filled(state, context, self.securities[symbol].price, 0.0, self.time)

    def _recover_entry_from_holding(self, state, source):
        if state.current_trade is not None:
            return
        if state.pending_entry is None and state.entry_signal_time is None:
            quantity = -self.portfolio[state.symbol].quantity
            if quantity != 0 and state.exit_order_id is None:
                self.debug(
                    "STATE_DESYNC_FLATTEN "
                    f"timestamp={self.time} symbol={state.ticker} reason_code=STATE_DESYNC_FLATTEN "
                    "detail=missing_entry_context"
                )
                self._submit_exit_order(state, "STATE_DESYNC_FLATTEN")
            return

        side = ""
        signal_time = None
        if state.pending_entry is not None:
            side = state.pending_entry["side"]
            signal_time = state.pending_entry["signal_time"]
        else:
            side = state.entry_side
            signal_time = state.entry_signal_time

        if signal_time is None or side == "":
            self._submit_exit_order(state, "STATE_DESYNC_FLATTEN")
            return

        holding = self.portfolio[state.symbol]
        fill_price = float(holding.average_price)
        if fill_price <= 0:
            fill_price = self.securities[state.symbol].price
        fill_qty = float(holding.quantity)
        fee = abs(fill_price * fill_qty * TAKER_FEE_RATE)
        context = {
            "type": "entry",
            "symbol": state.symbol,
            "side": side,
            "signal_time": signal_time,
            "quantity": fill_qty,
        }
        self._mark_entry_filled(state, context, fill_price, fill_qty, fee, self.time, source)

    def _submit_exit_order(self, state, reason_code):
        quantity = -self.portfolio[state.symbol].quantity
        if quantity == 0:
            return
        if state.exit_order_id is not None:
            return

        context = {
            "type": "exit",
            "symbol": state.symbol,
            "reason_code": reason_code,
        }
        self.active_submission_context = context
        ticket = self.market_order(state.symbol, quantity, tag=f"H0007_{reason_code}")
        self.order_id_to_context[ticket.order_id] = context
        if state.position_open:
            state.exit_order_id = ticket.order_id
        self.active_submission_context = None
        self.debug(
            "EXIT_ORDER_SUBMITTED "
            f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
            f"quantity={quantity} reason_code={reason_code} "
            f"entry_time={state.entry_time} holding_bars={state.bars_held}"
        )

    def _flatten_open_positions(self, reason_code):
        for symbol, state in self.states.items():
            if self.portfolio[symbol].invested:
                if not state.position_open:
                    self._recover_entry_from_holding(state, "END_RECONCILE")
                self._submit_exit_order(state, reason_code)
                if state.current_trade is not None:
                    fill_price = self.securities[symbol].price
                    fee = abs(fill_price * self.portfolio[symbol].quantity * TAKER_FEE_RATE)
                    context = {
                        "type": "exit",
                        "symbol": symbol,
                        "reason_code": reason_code,
                    }
                    self._mark_exit_filled(state, context, fill_price, fee, self.time)
