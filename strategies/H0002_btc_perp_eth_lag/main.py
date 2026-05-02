from AlgorithmImports import *
from datetime import timedelta
import math


# H0002_btc_perp_eth_lag
# QuantConnect Lean v17685 target.
# Verification required before full backtest:
# 1. Confirm BrokerageName.BINANCE is valid for Crypto Futures in the QC project.
# 2. Confirm AddCryptoFuture("BTCUSDT"/"ETHUSDT", market=Market.BINANCE)
#    maps to Binance USD-M perpetual futures, not spot or CFD data.
# 3. If either check fails, mark the strategy BLOCKED; do not proxy with spot.

BTC_IMPULSE_PCT = 0.35
ETH_MAX_SAMEBAR_MOVE_PCT = 0.12
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


class H0002BtcPerpEthLag(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2025, 1, 1)
        self.set_account_currency("USDT", 200)

        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)

        self.btc_security = self.add_crypto_future(
            "BTCUSDT",
            Resolution.MINUTE,
            market=Market.BINANCE,
            fill_forward=False,
            leverage=2,
        )
        self.eth_security = self.add_crypto_future(
            "ETHUSDT",
            Resolution.MINUTE,
            market=Market.BINANCE,
            fill_forward=False,
            leverage=2,
        )

        self.btc_symbol = self.btc_security.symbol
        self.eth_symbol = self.eth_security.symbol

        self.securities[self.btc_symbol].set_fee_model(BinanceTakerFeeModel())
        self.securities[self.eth_symbol].set_fee_model(BinanceTakerFeeModel())
        self.securities[self.btc_symbol].set_slippage_model(ConstantBpsSlippageModel(5.0))
        self.securities[self.eth_symbol].set_slippage_model(ConstantBpsSlippageModel(5.0))

        self.btc_5m = TradeBarConsolidator(timedelta(minutes=5))
        self.eth_5m = TradeBarConsolidator(timedelta(minutes=5))
        self.btc_5m.data_consolidated += self._on_btc_5m
        self.eth_5m.data_consolidated += self._on_eth_5m
        self.subscription_manager.add_consolidator(self.btc_symbol, self.btc_5m)
        self.subscription_manager.add_consolidator(self.eth_symbol, self.eth_5m)

        self.latest_btc_bar = None
        self.latest_eth_bar = None
        self.processed_signal_times = set()

        self.pending_signal = None
        self.active_trade = None
        self.entry_order_id = None
        self.exit_order_id = None
        self.exit_reason = None
        self.tracked_eth_order_ids = set()

        self.current_date = None
        self.daily_trade_count = 0
        self.daily_wins = 0
        self.daily_pre_fee_sum = 0.0
        self.daily_post_fee_sum = 0.0
        self.daily_full_friction_sum = 0.0
        self.daily_equity_peak = 0.0
        self.daily_max_drawdown_pct = 0.0

        self.debug(
            "INIT H0002 btc_perp_eth_lag "
            "params btc_impulse_pct=0.35 eth_max_samebar_move_pct=0.12 hold_bars=3 "
            "leverage=2 fee_per_side_pct=0.04 slippage_per_side_pct=0.05 "
            "expected_total_roundtrip_friction_pct=0.18"
        )

    def on_data(self, data):
        self._update_daily_state()
        self._validate_eth_state("on_data")

        if self.pending_signal is None:
            return
        if self.portfolio[self.eth_symbol].invested:
            return
        if self.eth_symbol not in data.bars:
            return

        eth_bar = data.bars[self.eth_symbol]
        if eth_bar.end_time <= self.pending_signal["signal_time"]:
            return

        direction = self.pending_signal["direction"]
        quantity = self._calculate_eth_quantity(direction, eth_bar.close)
        if quantity == 0:
            self.debug(
                "BLOCKED zero_quantity "
                f"time={self.time} eth_price={eth_bar.close:.8f} "
                f"lot_size={self.securities[self.eth_symbol].symbol_properties.lot_size}"
            )
            self.pending_signal = None
            return

        self.active_trade = {
            "btc_signal_time": self.pending_signal["btc_signal_time"],
            "eth_comparison_time": self.pending_signal["eth_comparison_time"],
            "eth_execution_time": eth_bar.end_time,
            "btc_impulse_pct": self.pending_signal["btc_impulse_pct"],
            "eth_samebar_move_pct": self.pending_signal["eth_samebar_move_pct"],
            "direction": direction,
            "entry_reference_price": eth_bar.close,
            "entry_fill_price": None,
            "entry_fill_algorithm_time": None,
            "holding_bars": 0,
            "entry_inferred": False,
            "exit_inferred": False,
            "logged_warnings": set(),
        }
        ticket = self.market_order(self.eth_symbol, quantity)
        self.entry_order_id = ticket.order_id
        self.tracked_eth_order_ids.add(ticket.order_id)
        side = "long" if direction > 0 else "short"
        self.debug(
            "ENTRY_SUBMITTED "
            f"btc_signal_ts={self.active_trade['btc_signal_time']} "
            f"eth_comparison_ts={self.active_trade['eth_comparison_time']} "
            f"planned_eth_execution_ts={self.active_trade['eth_execution_time']} "
            f"btc_impulse_pct={self.active_trade['btc_impulse_pct']:.4f} "
            f"eth_samebar_move_pct={self.active_trade['eth_samebar_move_pct']:.4f} "
            f"direction={side} entry_price_ref={eth_bar.close:.8f}"
        )
        self.pending_signal = None

    def on_order_event(self, order_event):
        is_eth_event = self._is_eth_order_event(order_event)
        if is_eth_event:
            self.debug(
                "ORDER_EVENT "
                f"time={self.time} "
                f"order_id={order_event.order_id} "
                f"symbol={order_event.symbol} "
                f"status={order_event.status} "
                f"fill_price={order_event.fill_price:.8f} "
                f"fill_quantity={order_event.fill_quantity} "
                f"direction={order_event.direction}"
            )
        if not is_eth_event:
            return
        if order_event.status != OrderStatus.FILLED:
            return

        if self.entry_order_id is not None and order_event.order_id == self.entry_order_id:
            if self.active_trade is not None:
                self.active_trade["entry_fill_price"] = order_event.fill_price
                self.active_trade["entry_fill_algorithm_time"] = self.time
                self.active_trade["holding_bars"] = 0
                self.debug(
                    "ENTRY_FILLED "
                    f"time={self.time} order_id={order_event.order_id} "
                    f"planned_eth_execution_ts={self.active_trade['eth_execution_time']} "
                    f"entry_fill_algorithm_time={self.active_trade['entry_fill_algorithm_time']} "
                    f"fill_price={order_event.fill_price:.8f} fill_qty={order_event.fill_quantity}"
                )
            self.entry_order_id = None
            return

        if self.exit_order_id is not None and order_event.order_id == self.exit_order_id:
            self._log_trade_exit(order_event.fill_price)
            self.exit_order_id = None
            self.exit_reason = None
            self.active_trade = None

    def _on_btc_5m(self, sender, bar):
        self.latest_btc_bar = bar
        self._try_create_signal()

    def _on_eth_5m(self, sender, bar):
        self.latest_eth_bar = bar
        self._validate_eth_state("eth_5m")
        self._infer_exit_if_flat("eth_5m")
        self._update_open_trade_holding(bar)
        self._try_create_signal()

    def _try_create_signal(self):
        if self.latest_btc_bar is None or self.latest_eth_bar is None:
            return
        if self.latest_btc_bar.end_time != self.latest_eth_bar.end_time:
            return
        if self.latest_btc_bar.end_time in self.processed_signal_times:
            return

        signal_time = self.latest_btc_bar.end_time
        self.processed_signal_times.add(signal_time)

        if self.pending_signal is not None:
            return
        if self.portfolio[self.eth_symbol].invested:
            return

        btc_move = self._bar_return_pct(self.latest_btc_bar)
        eth_move = self._bar_return_pct(self.latest_eth_bar)

        direction = 0
        if btc_move >= BTC_IMPULSE_PCT and eth_move <= ETH_MAX_SAMEBAR_MOVE_PCT:
            direction = 1
        elif btc_move <= -BTC_IMPULSE_PCT and eth_move >= -ETH_MAX_SAMEBAR_MOVE_PCT:
            direction = -1

        if direction == 0:
            return

        self.pending_signal = {
            "signal_time": signal_time,
            "btc_signal_time": self.latest_btc_bar.end_time,
            "eth_comparison_time": self.latest_eth_bar.end_time,
            "btc_impulse_pct": btc_move,
            "eth_samebar_move_pct": eth_move,
            "direction": direction,
        }
        side = "long" if direction > 0 else "short"
        self.debug(
            "SIGNAL "
            f"btc_signal_ts={self.latest_btc_bar.end_time} "
            f"eth_comparison_ts={self.latest_eth_bar.end_time} "
            f"btc_impulse_pct={btc_move:.4f} "
            f"eth_samebar_move_pct={eth_move:.4f} "
            f"direction={side}"
        )

    def _update_open_trade_holding(self, bar):
        if not self.portfolio[self.eth_symbol].invested:
            self._infer_exit_if_flat("holding_update")
            return
        if self.active_trade is None:
            self._liquidate_eth_for_state_error("missing_active_trade", "state_guard")
            return
        if self.exit_order_id is not None:
            return
        if bar.end_time <= self.active_trade["eth_execution_time"]:
            return

        self.active_trade["holding_bars"] += 1
        if self.active_trade["holding_bars"] > HOLD_BARS + 1:
            self._liquidate_eth_for_state_error("over_hold", "state_guard")
            return
        if self.active_trade["holding_bars"] >= HOLD_BARS:
            quantity = -self.portfolio[self.eth_symbol].quantity
            if quantity != 0:
                self.exit_reason = "time_exit"
                ticket = self.market_order(self.eth_symbol, quantity)
                self.exit_order_id = ticket.order_id
                self.tracked_eth_order_ids.add(ticket.order_id)
                self.debug(
                    "EXIT_SUBMITTED "
                    f"time={self.time} order_id={ticket.order_id} "
                    f"symbol={self.eth_symbol} quantity={quantity} "
                    f"holding_bars={self.active_trade['holding_bars']} "
                    f"exit_reason={self.exit_reason}"
                )

    def _calculate_eth_quantity(self, direction, price):
        notional = self.portfolio.total_portfolio_value * 2.0
        raw_quantity = notional / price
        lot_size = self.securities[self.eth_symbol].symbol_properties.lot_size
        rounded_quantity = math.floor(raw_quantity / lot_size) * lot_size
        return direction * rounded_quantity

    def _log_trade_exit(self, exit_price, log_label="TRADE_EXIT"):
        if self.active_trade is None:
            return

        entry_price = self.active_trade["entry_fill_price"]
        if entry_price is None:
            entry_price = self.active_trade["entry_reference_price"]

        direction = self.active_trade["direction"]
        pre_fee_pct = direction * ((exit_price / entry_price) - 1.0) * 100.0
        post_fee_estimate_pct = pre_fee_pct - 0.08
        full_friction_reference_pct = pre_fee_pct - 0.18
        side = "long" if direction > 0 else "short"
        win = post_fee_estimate_pct > 0

        self.daily_trade_count += 1
        self.daily_wins += 1 if win else 0
        self.daily_pre_fee_sum += pre_fee_pct
        self.daily_post_fee_sum += post_fee_estimate_pct
        self.daily_full_friction_sum += full_friction_reference_pct

        self.debug(
            f"{log_label} "
            f"btc_signal_ts={self.active_trade['btc_signal_time']} "
            f"eth_comparison_ts={self.active_trade['eth_comparison_time']} "
            f"planned_eth_execution_ts={self.active_trade['eth_execution_time']} "
            f"entry_fill_algorithm_time={self.active_trade['entry_fill_algorithm_time']} "
            f"btc_impulse_pct={self.active_trade['btc_impulse_pct']:.4f} "
            f"eth_samebar_move_pct={self.active_trade['eth_samebar_move_pct']:.4f} "
            f"direction={side} entry_price={entry_price:.8f} exit_price={exit_price:.8f} "
            f"holding_bars={self.active_trade['holding_bars']} "
            f"exit_reason={self.exit_reason} "
            f"pre_fee_pnl_pct={pre_fee_pct:.4f} "
            f"post_fee_estimate_pct={post_fee_estimate_pct:.4f} "
            f"full_friction_reference_pct={full_friction_reference_pct:.4f} "
            f"expected_total_roundtrip_friction_pct=0.18"
        )

    def _log_trade_exit_inferred(self, exit_price, source):
        if self.active_trade is None:
            return
        self.active_trade["exit_inferred"] = True
        if self.exit_reason is None:
            self.exit_reason = "time_exit_inferred_flat"
        self._log_trade_exit(exit_price, "TRADE_EXIT_INFERRED")
        self.exit_order_id = None
        self.exit_reason = None
        self.active_trade = None

    def _is_eth_order_event(self, order_event):
        if order_event.order_id in self.tracked_eth_order_ids:
            return True
        if order_event.symbol == self.eth_symbol:
            return True
        symbol_text = str(order_event.symbol)
        return "ETHUSDT" in symbol_text or "ETH" in symbol_text

    def _validate_eth_state(self, source):
        if not self.portfolio[self.eth_symbol].invested:
            self._infer_exit_if_flat(source)
            return
        if self.active_trade is None:
            self._liquidate_eth_for_state_error("missing_active_trade", source)
            return
        if self.active_trade["entry_fill_price"] is None:
            self._infer_entry_fill_from_holdings(source)
            return

    def _infer_entry_fill_from_holdings(self, source):
        holding = self.portfolio[self.eth_symbol]
        average_price = holding.average_price
        if average_price is None or average_price <= 0:
            self._log_trade_warning_once("invested_before_entry_fill_log", source)
            return

        self.active_trade["entry_fill_price"] = average_price
        self.active_trade["entry_fill_algorithm_time"] = self.time
        self.active_trade["holding_bars"] = 0
        self.active_trade["entry_inferred"] = True
        self.entry_order_id = None
        side = "long" if self.active_trade["direction"] > 0 else "short"
        self.debug(
            "ENTRY_FILLED_INFERRED "
            f"time={self.time} source={source} "
            f"planned_eth_execution_ts={self.active_trade['eth_execution_time']} "
            f"entry_fill_algorithm_time={self.active_trade['entry_fill_algorithm_time']} "
            f"entry_price={average_price:.8f} "
            f"quantity={holding.quantity} "
            f"direction={side}"
        )

    def _infer_exit_if_flat(self, source):
        if self.active_trade is None:
            return
        if self.portfolio[self.eth_symbol].invested:
            return
        if self.active_trade["entry_fill_price"] is None:
            return
        if self.active_trade["exit_inferred"]:
            return

        exit_price = self.securities[self.eth_symbol].price
        if exit_price is None or exit_price <= 0:
            exit_price = self.active_trade["entry_fill_price"]
        self._log_trade_exit_inferred(exit_price, source)

    def _log_trade_warning_once(self, warning_type, source):
        if self.active_trade is None:
            return
        logged_warnings = self.active_trade["logged_warnings"]
        if warning_type in logged_warnings:
            return
        logged_warnings.add(warning_type)
        self.debug(
            "STATE_WARNING "
            f"{warning_type} "
            f"time={self.time} source={source} "
            f"entry_order_id={self.entry_order_id} "
            f"quantity={self.portfolio[self.eth_symbol].quantity}"
        )

    def _liquidate_eth_for_state_error(self, reason, source):
        quantity = -self.portfolio[self.eth_symbol].quantity
        self.debug(
            "STATE_ERROR "
            f"time={self.time} source={source} reason={reason} "
            f"invested={self.portfolio[self.eth_symbol].invested} "
            f"quantity={self.portfolio[self.eth_symbol].quantity} "
            f"active_trade_present={self.active_trade is not None} "
            f"entry_order_id={self.entry_order_id} "
            f"exit_order_id={self.exit_order_id}"
        )
        if quantity == 0 or self.exit_order_id is not None:
            return
        self.exit_reason = f"state_error_{reason}"
        ticket = self.market_order(self.eth_symbol, quantity)
        self.exit_order_id = ticket.order_id
        self.tracked_eth_order_ids.add(ticket.order_id)
        self.entry_order_id = None
        self.debug(
            "EXIT_SUBMITTED "
            f"time={self.time} order_id={ticket.order_id} "
            f"symbol={self.eth_symbol} quantity={quantity} "
            f"holding_bars={self.active_trade['holding_bars'] if self.active_trade is not None else 'NA'} "
            f"exit_reason={self.exit_reason}"
        )

    def _update_daily_state(self):
        today = self.time.date()
        if self.current_date is None:
            self.current_date = today
            self.daily_equity_peak = self.portfolio.total_portfolio_value
            return

        if today != self.current_date:
            self._log_daily_summary()
            self.current_date = today
            self.daily_trade_count = 0
            self.daily_wins = 0
            self.daily_pre_fee_sum = 0.0
            self.daily_post_fee_sum = 0.0
            self.daily_full_friction_sum = 0.0
            self.daily_equity_peak = self.portfolio.total_portfolio_value
            self.daily_max_drawdown_pct = 0.0

        equity = self.portfolio.total_portfolio_value
        if equity > self.daily_equity_peak:
            self.daily_equity_peak = equity
        if self.daily_equity_peak > 0:
            drawdown_pct = (self.daily_equity_peak - equity) / self.daily_equity_peak * 100.0
            if drawdown_pct > self.daily_max_drawdown_pct:
                self.daily_max_drawdown_pct = drawdown_pct

    def _log_daily_summary(self):
        if self.daily_trade_count == 0:
            return

        win_rate = self.daily_wins / self.daily_trade_count * 100.0
        avg_pre_fee = self.daily_pre_fee_sum / self.daily_trade_count
        avg_post_fee = self.daily_post_fee_sum / self.daily_trade_count
        avg_full_friction = self.daily_full_friction_sum / self.daily_trade_count
        self.debug(
            "DAILY_SUMMARY "
            f"date={self.current_date} trade_count={self.daily_trade_count} "
            f"win_rate_pct={win_rate:.2f} "
            f"avg_pre_fee_edge_pct={avg_pre_fee:.4f} "
            f"avg_post_fee_estimate_pct={avg_post_fee:.4f} "
            f"avg_full_friction_reference_pct={avg_full_friction:.4f} "
            f"max_intraday_drawdown_pct={self.daily_max_drawdown_pct:.4f}"
        )

    def _bar_return_pct(self, bar):
        if bar.open == 0:
            return 0.0
        return (bar.close - bar.open) / bar.open * 100.0

    def on_end_of_algorithm(self):
        self._log_daily_summary()
