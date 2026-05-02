# H0008_funding_premium_crowding_unwind
#
# QuantConnect Lean v17685 assumptions:
# - BTCUSDT and ETHUSDT Binance USD-M perpetual futures are accessed with
#   add_crypto_future("BTCUSDT"/"ETHUSDT", Resolution.MINUTE, Market.BINANCE).
# - H0008 requires custom funding and premium-index data. QC-native availability
#   is NOT assumed. This file implements PythonData readers, but the user must
#   host or upload chronological CSV files and provide their URLs through QC
#   parameters before any valid H0008 backtest can trade.
# - Expected custom-data parameters:
#     H0008_FUNDING_BTCUSDT_URL, H0008_FUNDING_ETHUSDT_URL,
#     H0008_PREMIUM_BTCUSDT_URL, H0008_PREMIUM_ETHUSDT_URL.
#   If any URL is missing, the algorithm logs CUSTOM_DATA_PATH_MISSING and
#   disables trading rather than proxying the missing data.
#
# Friction model:
# - Custom taker fee model charges 0.04% per side.
# - Custom slippage model applies 0.05% per side.
# - Expected round-trip friction is about 0.08% fees + 0.10% slippage = 0.18%.

from AlgorithmImports import *
from datetime import datetime, timedelta
import math


# Exactly three H0008 free parameters.
FUNDING_REGIME_ABS_THRESHOLD = 0.0001
PREMIUM_COMPRESSION_PCT = 0.00015
HOLD_BARS = 3


# Fixed implementation/risk constants, not hypothesis tuning knobs.
TAKER_FEE_RATE = 0.0004
SLIPPAGE_RATE_PER_SIDE = 0.0005
MAX_PROJECT_DRAWDOWN = 0.20
STARTING_CASH_USDT = 200
LEVERAGE = 2.0
MARGIN_FRACTION_PER_SYMBOL = 0.45
BAR_MINUTES = 5
SMOKE_START_DATE = datetime(2024, 2, 29)
SMOKE_END_DATE = datetime(2024, 3, 3)
FINAL_LIQUIDATION_BUFFER_MINUTES = 10
DL0007_GAP_TIMES = {
    datetime(2024, 8, 12, 10, 2),
    datetime(2024, 8, 12, 10, 3),
}


def qc_utc_timezone():
    timezone = getattr(TimeZones, "Utc", None)
    if timezone is not None:
        return timezone
    return TimeZones.UTC


def qc_utc_always_open_exchange_hours():
    if hasattr(SecurityExchangeHours, "AlwaysOpen"):
        return SecurityExchangeHours.AlwaysOpen(qc_utc_timezone())
    return SecurityExchangeHours.always_open(qc_utc_timezone())


def h0008_symbol_properties(ticker):
    return SymbolProperties(f"{ticker} H0008 custom data", "USD", 1.0, 0.00000001, 1.0, ticker)


class BinanceFuturesTakerFeeModel(FeeModel):
    def _calculate_order_fee(self, parameters):
        security = parameters.security
        order = parameters.order
        price = security.price
        if price <= 0:
            price = order.price
        fee = abs(float(order.absolute_quantity) * float(price) * TAKER_FEE_RATE)
        return OrderFee(CashAmount(fee, "USDT"))

    def GetOrderFee(self, parameters):
        return self._calculate_order_fee(parameters)

    def get_order_fee(self, parameters):
        return self._calculate_order_fee(parameters)


class ConstantPercentSlippageModel:
    def _calculate_slippage(self, asset, order):
        return asset.price * SLIPPAGE_RATE_PER_SIDE

    def GetSlippageApproximation(self, asset, order):
        return self._calculate_slippage(asset, order)

    def get_slippage_approximation(self, asset, order):
        return self._calculate_slippage(asset, order)


def parse_utc_timestamp(value):
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1]
    for pattern in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            pass
    raise ValueError(f"Unsupported UTC timestamp format: {value}")


class H0008FundingRateData(PythonData):
    source_by_symbol = {}
    parse_error_count = 0
    last_parse_error = ""

    def GetSource(self, config, date, isLiveMode):
        url = H0008FundingRateData.source_by_symbol.get(config.Symbol.Value, "")
        return SubscriptionDataSource(url, SubscriptionTransportMedium.REMOTE_FILE)

    def DataTimeZone(self):
        return qc_utc_timezone()

    def data_time_zone(self):
        return qc_utc_timezone()

    def Reader(self, config, line, date, isLiveMode):
        if not line or line.startswith("timestamp_utc"):
            return None
        parts = line.split(",")
        if len(parts) < 6:
            H0008FundingRateData.record_parse_error(config.Symbol.Value, "column_count", line)
            return None
        try:
            data = H0008FundingRateData()
            data.Symbol = config.Symbol
            data.Time = parse_utc_timestamp(parts[0])
            data.EndTime = data.Time
            data.Value = float(parts[2])
            data["funding_rate"] = float(parts[2])
            data["mark_price_at_funding"] = 0.0 if parts[3] == "" else float(parts[3])
            data["source_symbol"] = parts[1]
            data["source_timestamp_utc"] = parts[0]
            return data
        except Exception as error:
            H0008FundingRateData.record_parse_error(config.Symbol.Value, str(error), line)
            return None

    @staticmethod
    def record_parse_error(symbol_value, reason, line):
        snippet = line[:180] if line is not None else ""
        H0008FundingRateData.parse_error_count += 1
        H0008FundingRateData.last_parse_error = (
            f"custom_symbol={symbol_value} reason={reason} line_snippet={snippet}"
        )

    def get_source(self, config, date, is_live_mode):
        return self.GetSource(config, date, is_live_mode)

    def reader(self, config, line, date, is_live_mode):
        return self.Reader(config, line, date, is_live_mode)


class H0008PremiumIndexData(PythonData):
    source_by_symbol = {}
    parse_error_count = 0
    last_parse_error = ""

    def GetSource(self, config, date, isLiveMode):
        url = H0008PremiumIndexData.source_by_symbol.get(config.Symbol.Value, "")
        return SubscriptionDataSource(url, SubscriptionTransportMedium.REMOTE_FILE)

    def DataTimeZone(self):
        return qc_utc_timezone()

    def data_time_zone(self):
        return qc_utc_timezone()

    def Reader(self, config, line, date, isLiveMode):
        if not line or line.startswith("timestamp_open_utc"):
            return None
        parts = line.split(",")
        if len(parts) < 9:
            H0008PremiumIndexData.record_parse_error(config.Symbol.Value, "column_count", line)
            return None
        try:
            data = H0008PremiumIndexData()
            data.Symbol = config.Symbol
            source_open_time = parse_utc_timestamp(parts[0])
            source_close_time = parse_utc_timestamp(parts[1])
            data.Time = source_open_time
            data.EndTime = source_close_time + timedelta(milliseconds=1)
            data.Value = float(parts[6])
            data["open"] = float(parts[3])
            data["high"] = float(parts[4])
            data["low"] = float(parts[5])
            data["close"] = float(parts[6])
            data["source_symbol"] = parts[2]
            data["source_timestamp_open_utc"] = parts[0]
            data["source_timestamp_close_utc"] = parts[1]
            return data
        except Exception as error:
            H0008PremiumIndexData.record_parse_error(config.Symbol.Value, str(error), line)
            return None

    @staticmethod
    def record_parse_error(symbol_value, reason, line):
        snippet = line[:180] if line is not None else ""
        H0008PremiumIndexData.parse_error_count += 1
        H0008PremiumIndexData.last_parse_error = (
            f"custom_symbol={symbol_value} reason={reason} line_snippet={snippet}"
        )

    def get_source(self, config, date, is_live_mode):
        return self.GetSource(config, date, is_live_mode)

    def reader(self, config, line, date, is_live_mode):
        return self.Reader(config, line, date, is_live_mode)


class FiveMinuteState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = None
        self.end_time = None
        self.count = 0
        self.open = 0.0
        self.high = 0.0
        self.low = 0.0
        self.close = 0.0

    def update(self, time, value):
        minute_floor = datetime(time.year, time.month, time.day, time.hour, time.minute)
        if time.second > 0 or time.microsecond > 0:
            minute_floor += timedelta(minutes=1)
        minutes_since_midnight = minute_floor.hour * 60 + minute_floor.minute
        if minutes_since_midnight == 0:
            bucket_end = minute_floor
        else:
            bucket_end_minutes = ((minutes_since_midnight + BAR_MINUTES - 1) // BAR_MINUTES) * BAR_MINUTES
            bucket_end = datetime(minute_floor.year, minute_floor.month, minute_floor.day) + timedelta(
                minutes=bucket_end_minutes
            )
        bucket = bucket_end - timedelta(minutes=BAR_MINUTES)
        if self.start_time is None:
            self.start_time = bucket
            self.end_time = bucket_end
            self.open = value
            self.high = value
            self.low = value
            self.close = value
            self.count = 1
            if self.count == BAR_MINUTES and minute_floor >= self.end_time:
                completed = self.as_completed_bar()
                self.reset()
                return completed
            return None
        if bucket != self.start_time:
            completed = self.as_completed_bar()
            self.start_time = bucket
            self.end_time = bucket_end
            self.open = value
            self.high = value
            self.low = value
            self.close = value
            self.count = 1
            return completed
        self.high = max(self.high, value)
        self.low = min(self.low, value)
        self.close = value
        self.count += 1
        if self.count == BAR_MINUTES and minute_floor >= self.end_time:
            completed = self.as_completed_bar()
            self.reset()
            return completed
        return None

    def as_completed_bar(self):
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "count": self.count,
        }


class SymbolState:
    def __init__(self, trade_symbol, ticker):
        self.trade_symbol = trade_symbol
        self.ticker = ticker
        self.funding_symbol = None
        self.premium_symbol = None
        self.latest_funding_time = None
        self.latest_funding_rate = None
        self.latest_premium_bar = None
        self.premium_builder = FiveMinuteState()
        self.price_bars_by_end = {}
        self.premium_bars_by_end = {}
        self.pending_entry = None
        self.pending_exit = False
        self.entry_order_id = None
        self.exit_order_id = None
        self.position_open = False
        self.entry_time = None
        self.entry_price = 0.0
        self.entry_quantity = 0.0
        self.entry_fee = 0.0
        self.bars_held = 0
        self.current_trade = None
        self.exit_submit_bars_held = None
        self.exit_retry_count = 0
        self.no_signal_missing_data = 0
        self.data_gap_flags = 0
        self.custom_data_seen = False
        self.first_funding_time = None
        self.last_funding_time_seen = None
        self.first_premium_time = None
        self.last_premium_time_seen = None
        self.logged_funding_first = False
        self.logged_premium_first = False
        self.logged_premium_5m_count = 0
        self.logged_price_5m_count = 0
        self.logged_missing_premium_count = 0
        self.logged_funding_custom_row_count = 0
        self.logged_premium_custom_row_count = 0
        self.logged_price_eval_count = 0
        self.logged_no_signal_condition_count = 0
        self.pending_price_bar_ends = []
        self.last_holding_bar_end_counted = None


class FundingPremiumCrowdingUnwind(QCAlgorithm):
    def initialize(self):
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(SMOKE_START_DATE.year, SMOKE_START_DATE.month, SMOKE_START_DATE.day)
        self.set_end_date(SMOKE_END_DATE.year, SMOKE_END_DATE.month, SMOKE_END_DATE.day)
        self.set_account_currency("USDT", STARTING_CASH_USDT)

        # Brokerage enum support for Binance USD-M Futures can vary by Lean version.
        # README contains the required smoke-test verification step.
        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)

        self.states = {}
        self.order_id_to_context = {}
        self.active_submission_context = None
        self.current_day = None
        self.day_stats = self._new_day_stats()
        self.project_peak = STARTING_CASH_USDT
        self.project_stop = False
        self.trading_disabled = False
        self.trading_disabled_reason = ""
        self.hard_drawdown_stop_triggered = False
        self.final_liquidation_started = False
        self.custom_data_invalid = False
        self.last_funding_parse_error_count = 0
        self.last_premium_parse_error_count = 0
        self.custom_data_ready = self._configure_custom_data_urls()

        for ticker in ["BTCUSDT", "ETHUSDT"]:
            security = self.add_crypto_future(
                ticker,
                Resolution.MINUTE,
                market=Market.BINANCE,
                fill_forward=False,
                leverage=LEVERAGE,
            )
            trade_symbol = security.symbol
            state = SymbolState(trade_symbol, ticker)
            self.states[trade_symbol] = state

            self.securities[trade_symbol].set_fee_model(BinanceFuturesTakerFeeModel())
            self.securities[trade_symbol].set_slippage_model(ConstantPercentSlippageModel())
            self.securities[trade_symbol].set_leverage(LEVERAGE)

            consolidator = TradeBarConsolidator(timedelta(minutes=BAR_MINUTES))
            consolidator.data_consolidated += self.on_five_minute_price_bar
            self.subscription_manager.add_consolidator(trade_symbol, consolidator)

            if self.custom_data_ready:
                custom_exchange_hours = qc_utc_always_open_exchange_hours()
                funding_ticker = f"H0008_FUNDING_{ticker}"
                premium_ticker = f"H0008_PREMIUM_{ticker}"
                funding = self.add_data(
                    H0008FundingRateData,
                    funding_ticker,
                    h0008_symbol_properties(funding_ticker),
                    custom_exchange_hours,
                )
                premium = self.add_data(
                    H0008PremiumIndexData,
                    premium_ticker,
                    h0008_symbol_properties(premium_ticker),
                    custom_exchange_hours,
                )
                state.funding_symbol = funding.symbol
                state.premium_symbol = premium.symbol

        if not self.custom_data_ready:
            self.trading_disabled = True
            self.trading_disabled_reason = "custom_data_path_missing"

        self.debug(
            "INIT H0008 params "
            f"funding_regime_abs_threshold={FUNDING_REGIME_ABS_THRESHOLD:.8f} "
            f"premium_compression_pct={PREMIUM_COMPRESSION_PCT:.8f} hold_bars={HOLD_BARS} "
            f"fee_per_side={TAKER_FEE_RATE:.4%} slippage_per_side={SLIPPAGE_RATE_PER_SIDE:.4%} "
            f"custom_data_ready={self.custom_data_ready}"
        )

    def on_data(self, slice):
        self._handle_day_rollover()
        self._update_project_drawdown()
        self._check_final_liquidation_window()
        self._cleanup_flat_stale_states("ON_DATA_FLAT_STALE")
        self._update_custom_data(slice)
        self._check_custom_data_parse_errors()
        self._evaluate_pending_price_bars()
        self._execute_pending_orders(slice)

    def on_five_minute_price_bar(self, sender, bar):
        state = self.states.get(bar.symbol)
        if state is None:
            return
        state.price_bars_by_end[bar.end_time] = bar
        self._trim_old_bars(state.price_bars_by_end, bar.end_time)
        if state.logged_price_5m_count < 10:
            state.logged_price_5m_count += 1

        if (
            state.position_open
            and state.entry_time is not None
            and bar.end_time > state.entry_time
            and state.last_holding_bar_end_counted != bar.end_time
        ):
            state.bars_held += 1
            state.last_holding_bar_end_counted = bar.end_time
            if state.bars_held >= HOLD_BARS and state.exit_order_id is None:
                self.debug(
                    "TIME_EXIT_DUE "
                    f"timestamp={self.time} symbol={state.ticker} bar_end={bar.end_time} "
                    f"bars_held={state.bars_held} hold_bars={HOLD_BARS} "
                    f"position_quantity={self.portfolio[state.trade_symbol].quantity}"
                )
                self._submit_exit_order(state, "TIME_EXIT")

            if (
                state.pending_exit
                and self.portfolio[state.trade_symbol].quantity != 0
                and state.exit_submit_bars_held is not None
                and state.bars_held >= state.exit_submit_bars_held + 2
            ):
                self._retry_stale_exit(state)

        if bar.end_time not in state.pending_price_bar_ends:
            state.pending_price_bar_ends.append(bar.end_time)

    def on_order_event(self, order_event):
        context = self.order_id_to_context.get(order_event.order_id)
        if context is None:
            context = self._context_from_active_submission(order_event)
        order_tag = self._order_tag(order_event.order_id)
        if (
            order_event.status == OrderStatus.FILLED
            or order_event.status == OrderStatus.INVALID
            or order_event.status == OrderStatus.CANCELED
        ):
            self.debug(
                "ORDER_EVENT "
                f"timestamp={self.time} order_id={order_event.order_id} symbol={order_event.symbol} "
                f"status={order_event.status} direction={order_event.direction} "
                f"fill_quantity={order_event.fill_quantity} fill_price={order_event.fill_price} "
                f"order_tag={order_tag}"
            )
        if context is None:
            return

        state = self.states[context["trade_symbol"]]
        if order_event.status == OrderStatus.INVALID or order_event.status == OrderStatus.CANCELED:
            if context["type"] == "entry":
                state.entry_order_id = None
                state.pending_entry = None
            if context["type"] == "exit":
                state.exit_order_id = None
                state.pending_exit = False
                state.exit_submit_bars_held = None
            return

        fill_price = float(order_event.fill_price)
        fill_qty = float(order_event.fill_quantity)
        if order_event.status != OrderStatus.FILLED and abs(fill_qty) <= 0:
            return

        fee = abs(fill_price * fill_qty * TAKER_FEE_RATE)
        if context["type"] == "entry":
            self._mark_entry_filled(state, context, fill_price, fill_qty, fee, self.time)
        elif context["type"] == "exit":
            self._mark_exit_filled(state, context, fill_price, fee, self.time)

    def on_end_of_algorithm(self):
        self._log_final_position_check("ON_END_BEFORE_FLATTEN")
        self._flatten_open_positions("FINAL_LIQUIDATION")
        for state in self.states.values():
            if self.portfolio[state.trade_symbol].quantity != 0:
                self.debug(
                    "FINAL_LIQUIDATION "
                    f"timestamp={self.time} symbol={state.ticker} reason_code=LIQUIDATE_FALLBACK "
                    f"position_quantity={self.portfolio[state.trade_symbol].quantity}"
                )
                self.liquidate(state.trade_symbol, "H0008_FINAL_LIQUIDATION")
        self._log_final_position_check("ON_END_AFTER_FLATTEN_REQUEST")
        self._log_daily_summary(force=True)

    def _configure_custom_data_urls(self):
        H0008FundingRateData.parse_error_count = 0
        H0008FundingRateData.last_parse_error = ""
        H0008PremiumIndexData.parse_error_count = 0
        H0008PremiumIndexData.last_parse_error = ""
        required = {
            "BTCUSDT_FUNDING": self.get_parameter("H0008_FUNDING_BTCUSDT_URL"),
            "ETHUSDT_FUNDING": self.get_parameter("H0008_FUNDING_ETHUSDT_URL"),
            "BTCUSDT_PREMIUM": self.get_parameter("H0008_PREMIUM_BTCUSDT_URL"),
            "ETHUSDT_PREMIUM": self.get_parameter("H0008_PREMIUM_ETHUSDT_URL"),
        }
        for key, value in required.items():
            if value is None or str(value).strip() == "":
                return False
            required[key] = str(value).strip()

        H0008FundingRateData.source_by_symbol = {
            "H0008_FUNDING_BTCUSDT": required["BTCUSDT_FUNDING"],
            "H0008_FUNDING_ETHUSDT": required["ETHUSDT_FUNDING"],
        }
        H0008PremiumIndexData.source_by_symbol = {
            "H0008_PREMIUM_BTCUSDT": required["BTCUSDT_PREMIUM"],
            "H0008_PREMIUM_ETHUSDT": required["ETHUSDT_PREMIUM"],
        }
        return True

    def _update_custom_data(self, slice):
        if not self.custom_data_ready:
            return

        for state in self.states.values():
            if state.funding_symbol is not None and slice.ContainsKey(state.funding_symbol):
                data = slice[state.funding_symbol]
                if data is not None:
                    state.latest_funding_time = data.time
                    state.latest_funding_rate = float(data["funding_rate"])
                    state.custom_data_seen = True
                    if state.first_funding_time is None:
                        state.first_funding_time = data.time
                    state.last_funding_time_seen = data.time
                    if not state.logged_funding_first:
                        state.logged_funding_first = True
                    if state.logged_funding_custom_row_count < 2:
                        state.logged_funding_custom_row_count += 1

            if state.premium_symbol is not None and slice.ContainsKey(state.premium_symbol):
                data = slice[state.premium_symbol]
                if data is not None:
                    if state.first_premium_time is None:
                        state.first_premium_time = data.time
                    state.last_premium_time_seen = data.time
                    if not state.logged_premium_first:
                        state.logged_premium_first = True
                    if state.logged_premium_custom_row_count < 2:
                        state.logged_premium_custom_row_count += 1
                    completed = state.premium_builder.update(data.end_time, float(data["close"]))
                    state.custom_data_seen = True
                    if completed is not None:
                        self._store_completed_premium_bar(state, completed)

    def _check_custom_data_parse_errors(self):
        funding_errors = H0008FundingRateData.parse_error_count
        premium_errors = H0008PremiumIndexData.parse_error_count
        if (
            funding_errors <= self.last_funding_parse_error_count
            and premium_errors <= self.last_premium_parse_error_count
        ):
            return

        self.last_funding_parse_error_count = funding_errors
        self.last_premium_parse_error_count = premium_errors
        self.custom_data_invalid = True
        self.project_stop = True
        self._flatten_open_positions("CUSTOM_DATA_INVALID_STOP")

    def _store_completed_premium_bar(self, state, completed):
        complete = completed["count"] == BAR_MINUTES
        if self._bar_intersects_dl0007_gap(completed["start_time"], completed["end_time"]):
            complete = False
            state.no_signal_missing_data += 1
            state.data_gap_flags += 1
        state.premium_bars_by_end[completed["end_time"]] = {
            "start_time": completed["start_time"],
            "end_time": completed["end_time"],
            "open": completed["open"],
            "close": completed["close"],
            "count": completed["count"],
            "complete": complete,
        }
        if state.logged_premium_5m_count < 3:
            state.logged_premium_5m_count += 1
        self._trim_old_bars(state.premium_bars_by_end, completed["end_time"])

    def _evaluate_pending_price_bars(self):
        for state in self.states.values():
            remaining = []
            for price_bar_end in state.pending_price_bar_ends:
                has_matching_premium = price_bar_end in state.premium_bars_by_end
                if state.logged_price_eval_count < 10:
                    state.logged_price_eval_count += 1
                if has_matching_premium:
                    self._create_signal_if_ready(state, price_bar_end)
                else:
                    remaining.append(price_bar_end)
            state.pending_price_bar_ends = remaining[-BAR_MINUTES:]

    def _create_signal_if_ready(self, state, price_bar_end):
        if self.trading_disabled:
            reason = (
                "trading_disabled_drawdown_stop"
                if self.trading_disabled_reason == "hard_drawdown_stop"
                else "trading_disabled"
            )
            self._log_signal_skipped(state, price_bar_end, reason)
            return
        if self.custom_data_invalid:
            self.day_stats["custom_data_missing"] += 1
            self._log_signal_skipped(state, price_bar_end, "trading_disabled")
            return
        if not self.custom_data_ready:
            self.day_stats["custom_data_missing"] += 1
            self._log_signal_skipped(state, price_bar_end, "trading_disabled")
            return
        if self.project_stop:
            reason = "end_flatten_window" if self.final_liquidation_started else "trading_disabled"
            self._log_signal_skipped(state, price_bar_end, reason)
            return
        if state.position_open:
            self._log_signal_skipped(state, price_bar_end, "already_in_position")
            return
        if state.pending_entry is not None:
            self._log_signal_skipped(state, price_bar_end, "pending_entry_exists")
            return
        if state.pending_exit or state.exit_order_id is not None:
            self._log_signal_skipped(state, price_bar_end, "pending_exit_exists")
            return
        if self.portfolio[state.trade_symbol].invested:
            self._log_signal_skipped(state, price_bar_end, "portfolio_invested")
            return

        if price_bar_end not in state.premium_bars_by_end:
            nearest_premium_bar_end = self._nearest_premium_bar_end(state, price_bar_end)
            if state.logged_missing_premium_count < 100:
                state.logged_missing_premium_count += 1
            state.no_signal_missing_data += 1
            self.day_stats["no_signal_count"] += 1
            return
        premium_bar = state.premium_bars_by_end[price_bar_end]
        if not premium_bar["complete"]:
            state.no_signal_missing_data += 1
            self.day_stats["no_signal_count"] += 1
            return

        price_bar = state.price_bars_by_end.get(price_bar_end)
        if price_bar is None:
            state.no_signal_missing_data += 1
            self.day_stats["no_signal_count"] += 1
            return

        if state.latest_funding_time is None or state.latest_funding_rate is None:
            self.day_stats["custom_data_missing"] += 1
            return
        if state.latest_funding_time > price_bar_end:
            state.no_signal_missing_data += 1
            self.day_stats["no_signal_count"] += 1
            return

        funding = state.latest_funding_rate
        premium_delta = premium_bar["close"] - premium_bar["open"]
        side = ""
        quantity_sign = 0
        if funding >= FUNDING_REGIME_ABS_THRESHOLD and premium_delta <= -PREMIUM_COMPRESSION_PCT:
            side = "short"
            quantity_sign = -1
        elif funding <= -FUNDING_REGIME_ABS_THRESHOLD and premium_delta >= PREMIUM_COMPRESSION_PCT:
            side = "long"
            quantity_sign = 1
        else:
            state.logged_no_signal_condition_count += 1
            if (
                state.logged_no_signal_condition_count <= 10
                or state.logged_no_signal_condition_count % 100 == 0
            ):
                self.debug(
                    "NO_SIGNAL_CONDITION "
                    f"algorithm_time={self.time} symbol={state.ticker} "
                    f"price_bar_end={price_bar_end} funding_regime_value={funding:.8f} "
                    f"premium_compression_value={premium_delta:.8f} "
                    f"funding_threshold_abs={FUNDING_REGIME_ABS_THRESHOLD:.8f} "
                    f"premium_threshold_abs={PREMIUM_COMPRESSION_PCT:.8f}"
                )
            return

        state.pending_entry = {
            "side": side,
            "quantity_sign": quantity_sign,
            "signal_bar_time": price_bar_end,
            "evaluation_time": self.time,
            "funding_time": state.latest_funding_time,
            "funding_rate": funding,
            "premium_compression": premium_delta,
        }
        self.debug(
            "SIGNAL "
            f"timestamp={self.time} symbol={state.ticker} side={side} evaluation_time={self.time} "
            f"signal_bar_time={price_bar_end} funding_time={state.latest_funding_time} "
            f"funding_regime_value={funding:.8f} premium_compression_value={premium_delta:.8f} "
            "reason_code=FUNDING_PREMIUM_CROWDING_UNWIND"
        )

    def _execute_pending_orders(self, slice):
        if self.project_stop or self.trading_disabled:
            for state in self.states.values():
                if state.pending_entry is not None:
                    if self.trading_disabled_reason == "hard_drawdown_stop":
                        reason = "trading_disabled_drawdown_stop"
                    else:
                        reason = "end_flatten_window" if self.final_liquidation_started else "trading_disabled"
                    self._clear_pending_entry_with_skip(state, reason)
            return

        for trade_symbol, state in self.states.items():
            if state.pending_exit or state.exit_order_id is not None:
                if state.pending_entry is not None:
                    self._clear_pending_entry_with_skip(state, "pending_exit_exists")
                continue

            if state.pending_entry is None or state.position_open or state.entry_order_id is not None:
                if state.pending_entry is not None and state.position_open:
                    self._clear_pending_entry_with_skip(state, "already_in_position")
                continue
            if self.time <= state.pending_entry["signal_bar_time"]:
                continue
            if self.time <= state.pending_entry.get("evaluation_time", state.pending_entry["signal_bar_time"]):
                continue
            if trade_symbol not in slice.bars:
                self._clear_pending_entry_with_skip(state, "missing_trade_symbol")
                continue

            price = self.securities[trade_symbol].price
            quantity = self._position_quantity(trade_symbol, price, state.pending_entry["quantity_sign"])
            if quantity == 0:
                self._clear_pending_entry_with_skip(state, "quantity_zero")
                continue

            context = {
                "type": "entry",
                "trade_symbol": trade_symbol,
                "side": state.pending_entry["side"],
                "signal_bar_time": state.pending_entry["signal_bar_time"],
                "evaluation_time": state.pending_entry["evaluation_time"],
                "funding_time": state.pending_entry["funding_time"],
                "funding_rate": state.pending_entry["funding_rate"],
                "premium_compression": state.pending_entry["premium_compression"],
            }
            self.active_submission_context = context
            ticket = self.market_order(trade_symbol, quantity, tag="H0008_ENTRY")
            self.order_id_to_context[ticket.order_id] = context
            state.entry_order_id = ticket.order_id
            self.active_submission_context = None
            self.debug(
                "ENTRY_ORDER_SUBMITTED "
                f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                f"side={context['side']} quantity={quantity} "
                f"signal_bar_time={context['signal_bar_time']} planned_execution_time={self.time}"
            )

    def _submit_exit_order(self, state, reason_code):
        current_qty = self.portfolio[state.trade_symbol].quantity
        quantity = -current_qty
        if quantity == 0 or state.exit_order_id is not None:
            return False
        context = {
            "type": "exit",
            "trade_symbol": state.trade_symbol,
            "reason_code": reason_code,
        }
        self.active_submission_context = context
        ticket = self.market_order(state.trade_symbol, quantity, tag=f"H0008_{reason_code}")
        self.order_id_to_context[ticket.order_id] = context
        state.exit_order_id = ticket.order_id
        state.pending_exit = True
        state.exit_submit_bars_held = state.bars_held
        self.active_submission_context = None
        self.debug(
            "EXIT_ORDER_SUBMITTED "
            f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
            f"exit_qty={quantity} current_portfolio_qty_before_submit={current_qty} "
            f"reason_code={reason_code} "
            f"entry_time={state.entry_time} holding_bars={state.bars_held}"
        )
        return True

    def _mark_entry_filled(self, state, context, fill_price, fill_qty, fee, fill_time):
        state.position_open = True
        state.entry_time = fill_time
        state.entry_price = fill_price
        state.entry_quantity = fill_qty
        state.entry_fee = fee
        state.bars_held = 0
        state.last_holding_bar_end_counted = None
        state.pending_entry = None
        state.entry_order_id = None
        state.current_trade = {
            "side": context["side"],
            "signal_bar_time": context["signal_bar_time"],
            "execution_bar_time": fill_time,
            "entry_price": fill_price,
            "entry_quantity": fill_qty,
            "entry_fee": fee,
            "funding_rate": context["funding_rate"],
            "premium_compression": context["premium_compression"],
        }
        delta_minutes = (fill_time - context["signal_bar_time"]).total_seconds() / 60.0
        self.debug(
            "ENTRY "
            f"timestamp={fill_time} symbol={state.ticker} side={context['side']} "
            f"signal_bar_time={context['signal_bar_time']} execution_bar_time={fill_time} "
            f"delta_minutes={delta_minutes:.1f} funding_regime_value={context['funding_rate']:.8f} "
            f"premium_compression_value={context['premium_compression']:.8f} entry_price={fill_price:.8f} "
            "reason_code=FUNDING_PREMIUM_CROWDING_UNWIND"
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

        self.day_stats["trade_count"] += 1
        self.day_stats["wins"] += 1 if post_fee_pct > 0 else 0
        self.day_stats["pre_fee_sum"] += pre_fee_pct
        self.day_stats["post_fee_sum"] += post_fee_pct

        delta_minutes = (trade["execution_bar_time"] - trade["signal_bar_time"]).total_seconds() / 60.0
        self.debug(
            "TRADE "
            f"timestamp={fill_time} symbol={state.ticker} side={side} "
            f"signal_bar_time={trade['signal_bar_time']} execution_bar_time={trade['execution_bar_time']} "
            f"delta_minutes={delta_minutes:.1f} funding_regime_value={trade['funding_rate']:.8f} "
            f"premium_compression_value={trade['premium_compression']:.8f} "
            f"entry_price={entry_price:.8f} exit_price={fill_price:.8f} holding_bars={state.bars_held} "
            f"reason_code={context['reason_code']} pre_fee_pnl_pct={pre_fee_pct:.5f} "
            f"post_fee_pnl_pct={post_fee_pct:.5f}"
        )
        self._clear_position_state(state)
        self.debug(
            "POSITION_CLEARED "
            f"timestamp={fill_time} symbol={state.ticker} reason_code={context['reason_code']} "
            f"portfolio_quantity={self.portfolio[state.trade_symbol].quantity} "
            f"position_open={state.position_open} pending_exit={state.pending_exit}"
        )

    def _log_signal_skipped(self, state, signal_bar_time, reason_code):
        self.debug(
            "SIGNAL_SKIPPED "
            f"timestamp={self.time} symbol={state.ticker} reason_code={reason_code} "
            f"signal_bar_time={signal_bar_time} position_open={state.position_open} "
            f"pending_entry_exists={state.pending_entry is not None} pending_exit={state.pending_exit} "
            f"entry_order_id={state.entry_order_id} exit_order_id={state.exit_order_id} "
            f"portfolio_invested={self.portfolio[state.trade_symbol].invested} "
            f"portfolio_quantity={self.portfolio[state.trade_symbol].quantity}"
        )

    def _clear_pending_entry_with_skip(self, state, reason_code):
        signal_bar_time = None
        if state.pending_entry is not None:
            signal_bar_time = state.pending_entry.get("signal_bar_time")
        self._log_signal_skipped(state, signal_bar_time, reason_code)
        state.pending_entry = None

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

    def _update_project_drawdown(self):
        equity = self.portfolio.total_portfolio_value
        if equity > self.project_peak:
            self.project_peak = equity
        drawdown = 0.0
        if self.project_peak > 0:
            drawdown = (self.project_peak - equity) / self.project_peak
        if drawdown > self.day_stats["max_intraday_drawdown"]:
            self.day_stats["max_intraday_drawdown"] = drawdown
        if drawdown >= MAX_PROJECT_DRAWDOWN and not self.hard_drawdown_stop_triggered:
            self._trigger_hard_drawdown_stop(drawdown)

    def _trigger_hard_drawdown_stop(self, drawdown):
        self.hard_drawdown_stop_triggered = True
        self.project_stop = True
        self.trading_disabled = True
        self.trading_disabled_reason = "hard_drawdown_stop"
        self.debug(
            "HARD_DRAWDOWN_STOP "
            f"timestamp={self.time} drawdown_from_peak_pct={drawdown * 100.0:.3f} "
            f"threshold_pct={MAX_PROJECT_DRAWDOWN * 100.0:.3f} "
            f"portfolio_value={self.portfolio.total_portfolio_value} peak_value={self.project_peak}"
        )
        for state in self.states.values():
            if state.pending_entry is not None:
                self._clear_pending_entry_with_skip(state, "trading_disabled_drawdown_stop")
        self._cancel_open_orders("HARD_DRAWDOWN_STOP")
        self._liquidate_all_positions("HARD_DRAWDOWN_STOP")

    def _cancel_open_orders(self, reason_code):
        open_orders = self.transactions.get_open_orders()
        for order in open_orders:
            try:
                self.transactions.cancel_order(order.id, reason_code)
            except Exception as error:
                pass

    def _liquidate_all_positions(self, reason_code):
        for state in self.states.values():
            quantity = self.portfolio[state.trade_symbol].quantity
            if quantity != 0:
                self.debug(
                    "FINAL_LIQUIDATION "
                    f"timestamp={self.time} symbol={state.ticker} reason_code={reason_code} "
                    f"position_quantity={quantity}"
                )
                self.liquidate(state.trade_symbol, reason_code)

    def _check_final_liquidation_window(self):
        if self.final_liquidation_started or self.trading_disabled:
            return
        final_liquidation_time = SMOKE_END_DATE - timedelta(minutes=FINAL_LIQUIDATION_BUFFER_MINUTES)
        if self.time < final_liquidation_time:
            return
        self.final_liquidation_started = True
        self.project_stop = True
        self.trading_disabled = True
        self.trading_disabled_reason = "end_flatten_window"
        self.debug(
            "FINAL_LIQUIDATION "
            f"timestamp={self.time} reason_code=PRE_END_FLATTEN "
            f"scheduled_end={SMOKE_END_DATE} buffer_minutes={FINAL_LIQUIDATION_BUFFER_MINUTES}"
        )
        self._flatten_open_positions("FINAL_LIQUIDATION")

    def _handle_day_rollover(self):
        today = self.time.date()
        if self.current_day is None:
            self.current_day = today
            return
        if today != self.current_day:
            self._log_daily_summary(force=True)
            self.current_day = today
            self.day_stats = self._new_day_stats()

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
        no_signal_count = self.day_stats["no_signal_count"] + sum(s.no_signal_missing_data for s in self.states.values())
        data_gap_flags = self.day_stats["data_gap_flags"] + sum(s.data_gap_flags for s in self.states.values())
        self.debug(
            "DAILY_SUMMARY "
            f"date={self.current_day} trade_count={trades} win_rate_pct={win_rate:.2f} "
            f"avg_pre_fee_edge_pct={avg_pre_fee:.5f} avg_post_fee_edge_pct={avg_post_fee:.5f} "
            f"max_intraday_drawdown_pct={self.day_stats['max_intraday_drawdown'] * 100.0:.2f} "
            f"no_signal_count={no_signal_count} data_gap_flags={data_gap_flags} "
            f"custom_data_ready={self.custom_data_ready} custom_data_missing_count={self.day_stats['custom_data_missing']}"
        )

    def _new_day_stats(self):
        return {
            "trade_count": 0,
            "wins": 0,
            "pre_fee_sum": 0.0,
            "post_fee_sum": 0.0,
            "max_intraday_drawdown": 0.0,
            "no_signal_count": 0,
            "data_gap_flags": 0,
            "custom_data_missing": 0,
        }

    def _bar_intersects_dl0007_gap(self, start_time, end_time):
        for gap_time in DL0007_GAP_TIMES:
            if start_time <= gap_time < end_time:
                return True
        return False

    def _nearest_premium_bar_end(self, state, price_bar_end):
        if not state.premium_bars_by_end:
            return None
        return min(
            state.premium_bars_by_end.keys(),
            key=lambda premium_end: abs((premium_end - price_bar_end).total_seconds()),
        )

    def _log_final_position_check(self, reason_code):
        self._cleanup_flat_stale_states(reason_code)
        for state in self.states.values():
            holding = self.portfolio[state.trade_symbol]
            self.debug(
                "FINAL_POSITION_CHECK "
                f"timestamp={self.time} reason_code={reason_code} symbol={state.ticker} "
                f"invested={holding.invested} quantity={holding.quantity} "
                f"holdings_value={holding.holdings_value} unrealized_profit={holding.unrealized_profit} "
                f"position_open={state.position_open} pending_exit={state.pending_exit} "
                f"entry_order_id={state.entry_order_id} exit_order_id={state.exit_order_id} "
                f"bars_held={state.bars_held} trading_disabled={self.trading_disabled} "
                f"trading_disabled_reason={self.trading_disabled_reason}"
            )

    def _cleanup_flat_stale_states(self, reason_code):
        for state in self.states.values():
            quantity = self.portfolio[state.trade_symbol].quantity
            if self.portfolio[state.trade_symbol].invested or abs(float(quantity)) > 0:
                continue
            if (
                state.position_open
                or state.pending_exit
                or state.entry_order_id is not None
                or state.exit_order_id is not None
                or state.bars_held != 0
            ):
                state.pending_exit = False
                state.entry_order_id = None
                state.exit_order_id = None
                state.position_open = False
                state.entry_time = None
                state.entry_price = 0.0
                state.entry_quantity = 0.0
                state.entry_fee = 0.0
                state.bars_held = 0
                state.last_holding_bar_end_counted = None
                state.exit_submit_bars_held = None
                state.exit_retry_count = 0
                state.current_trade = None

    def _retry_stale_exit(self, state):
        current_qty = self.portfolio[state.trade_symbol].quantity
        if current_qty == 0:
            return
        old_exit_order_id = state.exit_order_id
        if old_exit_order_id is not None:
            try:
                ticket = self.transactions.get_order_ticket(old_exit_order_id)
                if ticket is not None:
                    ticket.cancel("EXIT_STALE_RETRY")
            except Exception as error:
                pass
        state.exit_order_id = None
        state.pending_exit = False
        state.exit_submit_bars_held = None
        state.exit_retry_count += 1
        self._submit_exit_order(state, "TIME_EXIT_RETRY")

    def _order_tag(self, order_id):
        try:
            order = self.transactions.get_order_by_id(order_id)
            if order is not None:
                return order.tag
        except Exception:
            pass
        return ""

    def _trim_old_bars(self, bars, current_end):
        cutoff = current_end - timedelta(days=2)
        old_keys = [time for time in bars if time < cutoff]
        for key in old_keys:
            del bars[key]

    def _context_from_active_submission(self, order_event):
        context = self.active_submission_context
        if context is None:
            return None
        if order_event.symbol != context["trade_symbol"]:
            return None
        return context

    def _clear_position_state(self, state):
        state.pending_exit = False
        state.entry_order_id = None
        state.exit_order_id = None
        state.position_open = False
        state.entry_time = None
        state.entry_price = 0.0
        state.entry_quantity = 0.0
        state.entry_fee = 0.0
        state.bars_held = 0
        state.last_holding_bar_end_counted = None
        state.exit_submit_bars_held = None
        state.exit_retry_count = 0
        state.current_trade = None

    def _flatten_open_positions(self, reason_code):
        for state in self.states.values():
            if self.portfolio[state.trade_symbol].invested:
                self.debug(
                    "FINAL_LIQUIDATION "
                    f"timestamp={self.time} symbol={state.ticker} reason_code={reason_code} "
                    f"position_quantity={self.portfolio[state.trade_symbol].quantity} "
                    f"exit_order_id={state.exit_order_id}"
                )
                self._submit_exit_order(state, reason_code)
