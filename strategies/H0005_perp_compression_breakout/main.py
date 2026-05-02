from AlgorithmImports import *
from datetime import timedelta
import math


# H0005_perp_compression_breakout
# QuantConnect Lean v17685 target.
# Required manual verification:
# - BrokerageName.BINANCE with AddCryptoFuture must resolve BTCUSDT/ETHUSDT
#   as Binance Crypto Futures / USD-M perpetual-compatible data, not spot.
# - If symbol mapping fails, mark H0005 BLOCKED. Do not proxy with spot/CFD.

COMPRESSION_BARS = 12
MAX_COMPRESSION_RANGE_PCT = 0.35
HOLD_BARS = 3


class BinanceTakerFeeModel(FeeModel):
    def get_order_fee(self, parameters):
        fee = parameters.security.price * abs(parameters.order.absolute_quantity) * 0.0004
        return OrderFee(CashAmount(fee, "USDT"))


class ConstantBpsSlippageModel:
    def __init__(self, slippage_bps):
        self.slippage_rate = slippage_bps / 10000.0

    def get_slippage_approximation(self, asset, order):
        return asset.price * self.slippage_rate


class H0005PerpCompressionBreakout(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2024, 1, 8)
        self.set_account_currency("USDT", 200)
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)

        self.starting_equity = 200.0
        self.equity_peak = 200.0
        self.max_drawdown_pct = 0.0
        self.total_order_events = 0
        self.total_fees_seen = 0.0

        self.symbol_states = {}
        self.symbol_by_order_id = {}

        btc_security = self.add_crypto_future(
            "BTCUSDT",
            Resolution.MINUTE,
            market=Market.BINANCE,
            fill_forward=False,
            leverage=2,
        )
        eth_security = self.add_crypto_future(
            "ETHUSDT",
            Resolution.MINUTE,
            market=Market.BINANCE,
            fill_forward=False,
            leverage=2,
        )

        self._register_symbol("BTCUSDT", btc_security.symbol)
        self._register_symbol("ETHUSDT", eth_security.symbol)

        for state in self.symbol_states.values():
            security = self.securities[state["symbol"]]
            security.set_fee_model(BinanceTakerFeeModel())
            security.set_slippage_model(ConstantBpsSlippageModel(5.0))
            consolidator = TradeBarConsolidator(timedelta(minutes=5))
            consolidator.data_consolidated += self._make_5m_handler(state["symbol"])
            self.subscription_manager.add_consolidator(state["symbol"], consolidator)
            state["consolidator"] = consolidator

        self.debug(
            "INIT H0005_perp_compression_breakout "
            "version=2026-04-29 "
            "start=2024-01-01 end=2024-01-08 starting_cash=200 "
            "resolution=minute consolidated=5m "
            "compression_bars=12 max_compression_range_pct=0.35 hold_bars=3 "
            "leverage=2 sizing_rule=40pct_equity_at_2x_per_symbol "
            "fee_per_side_pct=0.04 slippage_per_side_pct=0.05 "
            "full_friction_reference_pct=0.18"
        )
        for state in self.symbol_states.values():
            self.debug(
                "SYMBOL_MAPPING "
                f"ticker={state['ticker']} symbol={state['symbol']} "
                f"security_type={self.securities[state['symbol']].type} "
                f"market={self.securities[state['symbol']].symbol.id.market}"
            )

    def _register_symbol(self, ticker, symbol):
        self.symbol_states[symbol] = {
            "ticker": ticker,
            "symbol": symbol,
            "bars": [],
            "pending_signal": None,
            "active_trade": None,
            "entry_order_id": None,
            "exit_order_id": None,
            "exit_reason": None,
            "consolidator": None,
            "bars_seen": 0,
            "compression_windows_checked": 0,
            "compression_detected_count": 0,
            "breakout_up_count": 0,
            "breakout_down_count": 0,
            "entry_submitted_count": 0,
            "entry_filled_or_inferred_count": 0,
            "exit_submitted_count": 0,
            "completed_trade_estimate": 0,
            "same_bar_execution_violations": 0,
            "insufficient_buying_power_errors": 0,
            "order_errors": 0,
            "margin_call_events": 0,
            "last_summary_date": None,
            "detailed_trade_logs": 0,
        }

    def _make_5m_handler(self, symbol):
        def handler(sender, bar):
            self._on_symbol_5m(symbol, bar)

        return handler

    def on_data(self, data):
        self._update_portfolio_drawdown()
        self._check_inferred_fills()

        for state in self.symbol_states.values():
            self._try_submit_pending_entry(state, data)

    def _on_symbol_5m(self, symbol, bar):
        state = self.symbol_states[symbol]
        state["bars_seen"] += 1
        self._check_inferred_fills()
        self._update_active_trade_holding(state, bar)

        completed_bars = state["bars"]
        if len(completed_bars) >= COMPRESSION_BARS:
            window = completed_bars[-COMPRESSION_BARS:]
            compression_high = max(item.high for item in window)
            compression_low = min(item.low for item in window)
            midpoint = (compression_high + compression_low) / 2.0
            compression_range_pct = 0.0
            if midpoint > 0:
                compression_range_pct = ((compression_high - compression_low) / midpoint) * 100.0

            state["compression_windows_checked"] += 1
            if compression_range_pct <= MAX_COMPRESSION_RANGE_PCT:
                state["compression_detected_count"] += 1
                self._evaluate_breakout(state, bar, compression_high, compression_low, compression_range_pct)

        completed_bars.append(bar)
        if len(completed_bars) > COMPRESSION_BARS + HOLD_BARS + 5:
            completed_bars.pop(0)

        self._maybe_log_periodic_summary(state, bar)

    def _evaluate_breakout(self, state, bar, compression_high, compression_low, compression_range_pct):
        if state["pending_signal"] is not None:
            return
        if state["active_trade"] is not None:
            return
        if self.portfolio[state["symbol"]].invested:
            return

        direction = 0
        if bar.close > compression_high:
            direction = 1
            state["breakout_up_count"] += 1
        elif bar.close < compression_low:
            direction = -1
            state["breakout_down_count"] += 1

        if direction == 0:
            return

        state["pending_signal"] = {
            "signal_algorithm_time": self.time,
            "signal_bar_end_time": bar.end_time,
            "planned_execution_algorithm_time": None,
            "planned_execution_bar_end_time": None,
            "direction": direction,
            "compression_high": compression_high,
            "compression_low": compression_low,
            "compression_range_pct": compression_range_pct,
            "breakout_close": bar.close,
        }

    def _try_submit_pending_entry(self, state, data):
        signal = state["pending_signal"]
        if signal is None:
            return
        if state["active_trade"] is not None or state["entry_order_id"] is not None:
            return
        if self.portfolio[state["symbol"]].invested:
            state["pending_signal"] = None
            return
        if state["symbol"] not in data.bars:
            return

        bar = data.bars[state["symbol"]]
        if bar.end_time <= signal["signal_bar_end_time"]:
            return

        quantity = self._calculate_order_quantity(state["symbol"], signal["direction"], bar.close)
        if quantity == 0:
            state["order_errors"] += 1
            self.debug(
                "ORDER_BLOCKED_ZERO_QTY "
                f"symbol={state['symbol']} time={self.time} price={bar.close:.8f} "
                f"lot_size={self.securities[state['symbol']].symbol_properties.lot_size}"
            )
            state["pending_signal"] = None
            return

        signal["planned_execution_algorithm_time"] = self.time
        signal["planned_execution_bar_end_time"] = bar.end_time
        state["active_trade"] = {
            "signal_algorithm_time": signal["signal_algorithm_time"],
            "signal_bar_end_time": signal["signal_bar_end_time"],
            "planned_execution_algorithm_time": signal["planned_execution_algorithm_time"],
            "planned_execution_bar_end_time": signal["planned_execution_bar_end_time"],
            "entry_fill_algorithm_time": None,
            "direction": signal["direction"],
            "compression_high": signal["compression_high"],
            "compression_low": signal["compression_low"],
            "compression_range_pct": signal["compression_range_pct"],
            "breakout_close": signal["breakout_close"],
            "entry_reference_price": bar.close,
            "entry_fill_price": None,
            "holding_bars": 0,
            "entry_inferred": False,
            "exit_inferred": False,
        }

        ticket = self.market_order(state["symbol"], quantity)
        state["entry_order_id"] = ticket.order_id
        self.symbol_by_order_id[ticket.order_id] = state["symbol"]
        state["entry_submitted_count"] += 1
        if signal["planned_execution_bar_end_time"] <= signal["signal_bar_end_time"]:
            state["same_bar_execution_violations"] += 1
            self.debug(
                "LEAKAGE_VIOLATION same_bar_execution "
                f"symbol={state['symbol']} "
                f"signal_bar_end_time={signal['signal_bar_end_time']} "
                f"planned_execution_bar_end_time={signal['planned_execution_bar_end_time']}"
            )
        state["pending_signal"] = None

    def _calculate_order_quantity(self, symbol, direction, price):
        equity = self.portfolio.total_portfolio_value
        notional = equity * 0.40 * 2.0
        raw_quantity = notional / price
        lot_size = self.securities[symbol].symbol_properties.lot_size
        rounded_quantity = math.floor(raw_quantity / lot_size) * lot_size
        return direction * rounded_quantity

    def _update_active_trade_holding(self, state, bar):
        trade = state["active_trade"]
        if trade is None:
            return
        if state["exit_order_id"] is not None:
            return
        if not self.portfolio[state["symbol"]].invested:
            self._infer_exit_if_flat(state, "holding_update")
            return
        if trade["entry_fill_price"] is None:
            self._infer_entry_if_invested(state, "holding_update")
            return
        if bar.end_time <= trade["planned_execution_bar_end_time"]:
            return

        trade["holding_bars"] += 1
        if trade["holding_bars"] >= HOLD_BARS:
            quantity = -self.portfolio[state["symbol"]].quantity
            if quantity == 0:
                self._infer_exit_if_flat(state, "zero_exit_quantity")
                return
            state["exit_reason"] = "time_exit"
            ticket = self.market_order(state["symbol"], quantity)
            state["exit_order_id"] = ticket.order_id
            self.symbol_by_order_id[ticket.order_id] = state["symbol"]
            state["exit_submitted_count"] += 1

    def on_order_event(self, order_event):
        self.total_order_events += 1
        symbol = self._resolve_order_event_symbol(order_event)
        if symbol is None:
            return

        state = self.symbol_states[symbol]
        message = str(order_event.message).lower()
        if "insufficient" in message and "buying power" in message:
            state["insufficient_buying_power_errors"] += 1
            self.debug(
                "INSUFFICIENT_BUYING_POWER "
                f"time={self.time} symbol={symbol} order_id={order_event.order_id} "
                f"status={order_event.status} message={order_event.message}"
            )
        if order_event.status == OrderStatus.INVALID:
            state["order_errors"] += 1
            self.debug(
                "ORDER_ERROR "
                f"time={self.time} symbol={symbol} order_id={order_event.order_id} "
                f"status={order_event.status} message={order_event.message}"
            )
            if state["entry_order_id"] == order_event.order_id:
                state["entry_order_id"] = None
                state["active_trade"] = None
            if state["exit_order_id"] == order_event.order_id:
                state["exit_order_id"] = None
            return
        if order_event.status == OrderStatus.CANCELED:
            state["order_errors"] += 1
            self.debug(
                "ORDER_ERROR "
                f"time={self.time} symbol={symbol} order_id={order_event.order_id} "
                f"status={order_event.status} message={order_event.message}"
            )
            return
        if order_event.status != OrderStatus.FILLED:
            return

        if state["entry_order_id"] == order_event.order_id:
            self._mark_entry_filled(state, order_event.fill_price, self.time, False)
            state["entry_order_id"] = None
            return

        if state["exit_order_id"] == order_event.order_id:
            self._log_trade_exit(state, order_event.fill_price, "TRADE_EXIT")
            state["exit_order_id"] = None
            state["exit_reason"] = None
            state["active_trade"] = None

    def _resolve_order_event_symbol(self, order_event):
        if order_event.order_id in self.symbol_by_order_id:
            return self.symbol_by_order_id[order_event.order_id]
        if order_event.symbol in self.symbol_states:
            return order_event.symbol
        symbol_text = str(order_event.symbol)
        for state in self.symbol_states.values():
            if state["ticker"] in symbol_text:
                return state["symbol"]
        return None

    def _check_inferred_fills(self):
        for state in self.symbol_states.values():
            if state["active_trade"] is not None and self.portfolio[state["symbol"]].invested:
                if state["active_trade"]["entry_fill_price"] is None:
                    self._infer_entry_if_invested(state, "portfolio_holding")
            if state["active_trade"] is not None and not self.portfolio[state["symbol"]].invested:
                self._infer_exit_if_flat(state, "portfolio_flat")

    def _infer_entry_if_invested(self, state, source):
        trade = state["active_trade"]
        if trade is None:
            return
        holding = self.portfolio[state["symbol"]]
        average_price = holding.average_price
        if average_price is None or average_price <= 0:
            return
        self._mark_entry_filled(state, average_price, self.time, True)
        state["entry_order_id"] = None

    def _mark_entry_filled(self, state, fill_price, fill_time, inferred):
        trade = state["active_trade"]
        if trade is None:
            return
        if trade["entry_fill_price"] is not None:
            return
        trade["entry_fill_price"] = fill_price
        trade["entry_fill_algorithm_time"] = fill_time
        trade["entry_inferred"] = inferred
        trade["holding_bars"] = 0
        state["entry_filled_or_inferred_count"] += 1

    def _infer_exit_if_flat(self, state, source):
        trade = state["active_trade"]
        if trade is None:
            return
        if trade["entry_fill_price"] is None:
            return
        if trade["exit_inferred"]:
            return
        exit_price = self.securities[state["symbol"]].price
        if exit_price is None or exit_price <= 0:
            exit_price = trade["entry_fill_price"]
        trade["exit_inferred"] = True
        if state["exit_reason"] is None:
            state["exit_reason"] = "time_exit_inferred_flat"
        self._log_trade_exit(state, exit_price, "TRADE_EXIT_INFERRED")
        state["exit_order_id"] = None
        state["exit_reason"] = None
        state["active_trade"] = None

    def _log_trade_exit(self, state, exit_price, log_label):
        trade = state["active_trade"]
        if trade is None:
            return
        entry_price = trade["entry_fill_price"]
        if entry_price is None or entry_price <= 0:
            entry_price = trade["entry_reference_price"]
        direction = trade["direction"]
        pre_fee_pct = direction * ((exit_price / entry_price) - 1.0) * 100.0
        post_fee_estimate_pct = pre_fee_pct - 0.08
        full_friction_reference_pct = pre_fee_pct - 0.18
        side = "long" if direction > 0 else "short"
        state["completed_trade_estimate"] += 1
        should_log_detail = state["detailed_trade_logs"] < 3
        if should_log_detail:
            state["detailed_trade_logs"] += 1
        else:
            return
        self.debug(
            f"{log_label} "
            f"symbol={state['symbol']} ticker={state['ticker']} direction={side} "
            f"signal_algorithm_time={trade['signal_algorithm_time']} "
            f"signal_bar_end_time={trade['signal_bar_end_time']} "
            f"planned_execution_algorithm_time={trade['planned_execution_algorithm_time']} "
            f"planned_execution_bar_end_time={trade['planned_execution_bar_end_time']} "
            f"entry_fill_algorithm_time={trade['entry_fill_algorithm_time']} "
            f"entry_price={entry_price:.8f} exit_price={exit_price:.8f} "
            f"holding_bars={trade['holding_bars']} exit_reason={state['exit_reason']} "
            f"compression_range_pct={trade['compression_range_pct']:.4f} "
            f"pre_fee_pnl_pct={pre_fee_pct:.4f} "
            f"post_fee_estimate_pct={post_fee_estimate_pct:.4f} "
            f"full_friction_reference_pct={full_friction_reference_pct:.4f}"
        )

    def _maybe_log_periodic_summary(self, state, bar):
        bar_date = bar.end_time.date()
        if state["last_summary_date"] is None:
            state["last_summary_date"] = bar_date
            return
        if bar_date == state["last_summary_date"]:
            return
        self._log_symbol_summary(state, "DAILY_SYMBOL_SUMMARY")
        state["last_summary_date"] = bar_date

    def _log_symbol_summary(self, state, label):
        self.debug(
            f"{label} "
            f"symbol={state['symbol']} ticker={state['ticker']} "
            f"bars_seen={state['bars_seen']} "
            f"compression_windows_checked={state['compression_windows_checked']} "
            f"compression_detected_count={state['compression_detected_count']} "
            f"breakout_up_count={state['breakout_up_count']} "
            f"breakout_down_count={state['breakout_down_count']} "
            f"entry_submitted_count={state['entry_submitted_count']} "
            f"entry_filled_or_inferred_count={state['entry_filled_or_inferred_count']} "
            f"exit_submitted_count={state['exit_submitted_count']} "
            f"completed_trade_estimate={state['completed_trade_estimate']} "
            f"same_bar_execution_violations={state['same_bar_execution_violations']} "
            f"insufficient_buying_power_errors={state['insufficient_buying_power_errors']} "
            f"order_errors={state['order_errors']} "
            f"margin_call_events={state['margin_call_events']} "
            f"final_quantity={self.portfolio[state['symbol']].quantity}"
        )

    def _update_portfolio_drawdown(self):
        equity = self.portfolio.total_portfolio_value
        if equity > self.equity_peak:
            self.equity_peak = equity
        if self.equity_peak > 0:
            drawdown_pct = (self.equity_peak - equity) / self.equity_peak * 100.0
            if drawdown_pct > self.max_drawdown_pct:
                self.max_drawdown_pct = drawdown_pct

    def on_margin_call_warning(self):
        self.debug(f"MARGIN_CALL_WARNING time={self.time}")
        for state in self.symbol_states.values():
            state["margin_call_events"] += 1

    def on_margin_call(self, requests):
        self.debug(f"MARGIN_CALL time={self.time} request_count={len(requests)}")
        for state in self.symbol_states.values():
            state["margin_call_events"] += 1
        return requests

    def on_end_of_algorithm(self):
        final_equity = self.portfolio.total_portfolio_value
        net_return_pct = 0.0
        if self.starting_equity > 0:
            net_return_pct = ((final_equity / self.starting_equity) - 1.0) * 100.0
        for state in self.symbol_states.values():
            self._log_symbol_summary(state, "FINAL_SYMBOL_SUMMARY")
            if state["completed_trade_estimate"] < 300:
                self.debug(
                    "FALSIFICATION_WARNING "
                    f"symbol={state['symbol']} completed_trade_estimate={state['completed_trade_estimate']} "
                    "intraday_minimum=300"
                )
        self.debug(
            "FINAL_PORTFOLIO_SUMMARY "
            f"start_equity={self.starting_equity:.2f} "
            f"final_equity={final_equity:.2f} "
            f"net_return_pct={net_return_pct:.4f} "
            f"max_drawdown_pct={self.max_drawdown_pct:.4f} "
            f"total_order_events={self.total_order_events} "
            "total_fees_if_available=see_QC_orders_statistics"
        )
