# PROFILE: B-Position
from AlgorithmImports import *
from collections import deque
from datetime import datetime, timedelta
import math


FUNDING_EXTREME_ZSCORE: float = 2.0
HOLD_HOURS: int = 72
PER_TRADE_STOP_FRAC: float = 0.01


TIER_M_PER_SIDE_FEE: float = 0.0002
MAKER_DEFAULT_ADVERSE_THRESHOLD_BP: float = 5.0
DRAWDOWN_HARD_STOP_FRAC: float = 0.20
TRADE_LOG_PREFIX: str = "TRADE"
DAILY_SUMMARY_PREFIX: str = "DAILY_SUMMARY"


def parse_utc_timestamp(value):
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1]
    for pattern in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            pass
    raise ValueError("Unsupported UTC timestamp format: " + value)


class BinanceUMMakerFeeModel(FeeModel):
    """
    Tier M fee: 0.02 percent of order notional per side. No rebate.
    """

    PER_SIDE_RATE: float = 0.0002
    TIER: str = "M"

    def _order_fee(self, parameters):
        quantity = abs(float(parameters.order.quantity))
        price = float(parameters.security.price)
        if price <= 0.0:
            price = float(parameters.order.price)
        fee = self.PER_SIDE_RATE * quantity * price
        return OrderFee(CashAmount(fee, "USD"))

    def GetOrderFee(self, parameters):
        return self._order_fee(parameters)

    def get_order_fee(self, parameters):
        return self._order_fee(parameters)


class _PendingSignal:
    def __init__(self, side, limit_price, quantity, context):
        self.side = int(side)
        self.limit_price = float(limit_price)
        self.quantity = float(quantity)
        self.context = context


class FillDecision:
    def __init__(self, action, signed_quantity=0.0, fill_price=0.0, context=None):
        self.action = str(action)
        self.signed_quantity = float(signed_quantity)
        self.fill_price = float(fill_price)
        self.context = context


class MakerSignalGate:
    """
    Filters maker entry signals through the adverse-selection rule:
    the next bar must touch the limit and then close at least 0.05
    percent adverse to the fill side.
    """

    DEFAULT_ADVERSE_THRESHOLD_BP: float = MAKER_DEFAULT_ADVERSE_THRESHOLD_BP

    def __init__(self, adverse_threshold_bp=None):
        threshold = self.DEFAULT_ADVERSE_THRESHOLD_BP
        if adverse_threshold_bp is not None:
            threshold = float(adverse_threshold_bp)
        if threshold < 0.0:
            raise ValueError("adverse_threshold_bp must be non-negative")
        self._threshold_frac = threshold / 10000.0
        self._pending = {}

    @property
    def adverse_threshold_bp(self):
        return self._threshold_frac * 10000.0

    def has_pending(self, symbol):
        return symbol in self._pending

    def submit(self, symbol, side, limit_price, quantity, context):
        if side not in (-1, 1):
            raise ValueError("side must be +1 or -1")
        if limit_price <= 0.0:
            raise ValueError("limit_price must be positive")
        if quantity <= 0.0:
            raise ValueError("quantity must be positive")
        self._pending[symbol] = _PendingSignal(side, limit_price, quantity, context)

    def cancel(self, symbol):
        if symbol in self._pending:
            del self._pending[symbol]

    def resolve(self, symbol, bar):
        pending = self._pending.get(symbol)
        if pending is None:
            return FillDecision(action="pending")

        low = float(bar.low)
        high = float(bar.high)
        close = float(bar.close)
        side = pending.side
        limit = pending.limit_price

        touched = (side > 0 and low <= limit) or (side < 0 and high >= limit)
        if not touched:
            del self._pending[symbol]
            return FillDecision(action="pending", context=pending.context)

        if side > 0:
            adverse = close <= limit * (1.0 - self._threshold_frac)
        else:
            adverse = close >= limit * (1.0 + self._threshold_frac)

        del self._pending[symbol]

        if not adverse:
            return FillDecision(action="expire", context=pending.context)

        signed_quantity = float(side) * pending.quantity
        return FillDecision(
            action="fill",
            signed_quantity=signed_quantity,
            fill_price=limit,
            context=pending.context,
        )


class BinanceUMMakerFillModel:
    TIER: str = "M"


class DrawdownStop:
    DEFAULT_HARD_STOP_FRAC: float = DRAWDOWN_HARD_STOP_FRAC

    def __init__(self, hard_stop_frac=None):
        frac = self.DEFAULT_HARD_STOP_FRAC
        if hard_stop_frac is not None:
            frac = float(hard_stop_frac)
        if not 0.0 < frac <= self.DEFAULT_HARD_STOP_FRAC:
            raise ValueError("hard_stop_frac must be in (0, 0.20]")
        self._frac = frac
        self._peak = None
        self._tripped = False

    @property
    def hard_stop_frac(self):
        return self._frac

    @property
    def peak(self):
        return self._peak

    @property
    def tripped(self):
        return self._tripped

    def update(self, equity):
        equity = float(equity)
        if self._peak is None or equity > self._peak:
            self._peak = equity
        if self._peak is not None and self._peak > 0.0:
            drawdown = (self._peak - equity) / self._peak
            if drawdown >= self._frac:
                self._tripped = True
        return self._tripped

    def reset(self):
        self._peak = None
        self._tripped = False


class TradeRecord:
    def __init__(
        self,
        timestamp,
        symbol,
        side,
        entry_price,
        exit_price,
        holding_bars,
        reason,
        pre_fee_pnl,
        post_fee_pnl,
    ):
        self.timestamp = timestamp
        self.symbol = symbol
        self.side = int(side)
        self.entry_price = float(entry_price)
        self.exit_price = float(exit_price)
        self.holding_bars = int(holding_bars)
        self.reason = str(reason)
        self.pre_fee_pnl = float(pre_fee_pnl)
        self.post_fee_pnl = float(post_fee_pnl)


class PerTradeLogger:
    PREFIX: str = TRADE_LOG_PREFIX

    def __init__(self, emit):
        self._emit = emit
        self._records = []

    @property
    def records(self):
        return list(self._records)

    def record(
        self,
        timestamp,
        symbol,
        side,
        entry_price,
        exit_price,
        holding_bars,
        reason,
        pre_fee_pnl,
        post_fee_pnl,
    ):
        record = TradeRecord(
            timestamp,
            symbol,
            side,
            entry_price,
            exit_price,
            holding_bars,
            reason,
            pre_fee_pnl,
            post_fee_pnl,
        )
        self._records.append(record)
        self._emit(self._format(record))

    def _format(self, r):
        return (
            f"{self.PREFIX} ts={r.timestamp} sym={r.symbol} side={r.side} "
            f"entry={r.entry_price:.6f} exit={r.exit_price:.6f} "
            f"bars={r.holding_bars} reason={r.reason} "
            f"pre_fee_pnl={r.pre_fee_pnl:.6f} "
            f"post_fee_pnl={r.post_fee_pnl:.6f}"
        )


class _DayBucket:
    def __init__(self):
        self.trade_count = 0
        self.wins = 0
        self.pre_fee_pnl_sum = 0.0
        self.post_fee_pnl_sum = 0.0
        self.intraday_peak = 0.0
        self.intraday_max_dd = 0.0


class DailySummary:
    PREFIX: str = DAILY_SUMMARY_PREFIX

    def __init__(self, emit):
        self._emit = emit
        self._bucket = _DayBucket()

    def on_trade(self, pre_fee_pnl, post_fee_pnl):
        self._bucket.trade_count += 1
        if post_fee_pnl > 0.0:
            self._bucket.wins += 1
        self._bucket.pre_fee_pnl_sum += float(pre_fee_pnl)
        self._bucket.post_fee_pnl_sum += float(post_fee_pnl)

    def on_equity(self, equity):
        equity = float(equity)
        if equity > self._bucket.intraday_peak:
            self._bucket.intraday_peak = equity
        if self._bucket.intraday_peak > 0.0:
            dd = (self._bucket.intraday_peak - equity) / self._bucket.intraday_peak
            if dd > self._bucket.intraday_max_dd:
                self._bucket.intraday_max_dd = dd

    def flush(self, date):
        b = self._bucket
        win_rate = (b.wins / b.trade_count) if b.trade_count > 0 else 0.0
        avg_pre = (b.pre_fee_pnl_sum / b.trade_count) if b.trade_count > 0 else 0.0
        avg_post = (b.post_fee_pnl_sum / b.trade_count) if b.trade_count > 0 else 0.0
        self._emit(
            f"{self.PREFIX} date={date} trades={b.trade_count} "
            f"win_rate={win_rate:.4f} "
            f"avg_pre_fee={avg_pre:.6f} avg_post_fee={avg_post:.6f} "
            f"intraday_max_dd={b.intraday_max_dd:.4f}"
        )
        self._bucket = _DayBucket()


class H0009FundingRateData(PythonData):
    source_by_symbol = {}
    parse_error_count = 0
    last_parse_error = ""

    def GetSource(self, config, date, isLiveMode):
        url = H0009FundingRateData.source_by_symbol.get(config.Symbol.Value, "")
        return SubscriptionDataSource(url, SubscriptionTransportMedium.REMOTE_FILE)

    def DataTimeZone(self):
        return TimeZones.UTC

    def data_time_zone(self):
        return TimeZones.UTC

    def Reader(self, config, line, date, isLiveMode):
        if line is None or line == "" or line.startswith("timestamp"):
            return None
        parts = line.split(",")
        if len(parts) < 3:
            H0009FundingRateData.record_parse_error(config.Symbol.Value, "column_count", line)
            return None
        try:
            data = H0009FundingRateData()
            data.Symbol = config.Symbol
            data.Time = parse_utc_timestamp(parts[0])
            data.EndTime = data.Time
            data.Value = float(parts[2])
            data["funding_rate"] = float(parts[2])
            data["source_symbol"] = parts[1]
            data["source_timestamp_utc"] = parts[0]
            return data
        except Exception as error:
            H0009FundingRateData.record_parse_error(config.Symbol.Value, str(error), line)
            return None

    @staticmethod
    def record_parse_error(symbol_value, reason, line):
        snippet = line[:180] if line is not None else ""
        H0009FundingRateData.parse_error_count += 1
        H0009FundingRateData.last_parse_error = (
            f"custom_symbol={symbol_value} reason={reason} line_snippet={snippet}"
        )

    def get_source(self, config, date, is_live_mode):
        return self.GetSource(config, date, is_live_mode)

    def reader(self, config, line, date, is_live_mode):
        return self.Reader(config, line, date, is_live_mode)


class SymbolState:
    def __init__(self, ticker, trade_symbol):
        self.ticker = ticker
        self.trade_symbol = trade_symbol
        self.funding_symbol = None
        self.funding_history = deque(maxlen=90)
        self.last_funding_time = None
        self.last_price_bar = None
        self.entry_time = None
        self.entry_price = 0.0
        self.entry_quantity = 0.0
        self.entry_fee = 0.0
        self.entry_side = 0
        self.signal_time = None
        self.execution_time = None
        self.funding_time = None
        self.funding_rate = 0.0
        self.funding_zscore = 0.0
        self.bars_held = 0
        self.last_hold_bar_time = None
        self.entry_order_id = None
        self.exit_order_id = None
        self.position_open = False
        self.no_signal_count = 0
        self.signals = 0


class FundExtremeCrossSymbolContinuation(QCAlgorithm):
    def initialize(self):
        self.set_time_zone(TimeZones.UTC)
        self.set_start_date(2024, 1, 1)
        self.set_end_date(2026, 5, 2)
        self.set_cash(200)
        self.set_account_currency("USD", 200)

        self.set_brokerage_model(BrokerageName.BINANCE, AccountType.MARGIN)

        self.states = {}
        self.funding_to_trade_symbol = {}
        self.order_context = {}
        self.active_order_context = None
        self.maker_gate = MakerSignalGate()
        self.drawdown_stop = DrawdownStop()
        self.trade_logger = PerTradeLogger(self.debug)
        self.daily_summary = DailySummary(self.debug)
        self.current_day = None
        self.trading_disabled = False
        self.trading_disabled_reason = ""
        self.custom_data_ready = self._configure_custom_data()

        for ticker in ["BTCUSDT", "ETHUSDT"]:
            security = self.add_crypto_future(
                ticker,
                Resolution.HOUR,
                market=Market.BINANCE,
                fill_forward=False,
                leverage=2.0,
            )
            trade_symbol = security.symbol
            self.securities[trade_symbol].set_fee_model(BinanceUMMakerFeeModel())
            self.securities[trade_symbol].set_leverage(2.0)
            state = SymbolState(ticker, trade_symbol)
            self.states[trade_symbol] = state

            if self.custom_data_ready:
                funding_ticker = "H0009_FUNDING_" + ticker
                funding = self.add_data(H0009FundingRateData, funding_ticker, Resolution.HOUR)
                state.funding_symbol = funding.symbol
                self.funding_to_trade_symbol[funding.symbol] = trade_symbol

        if not self.custom_data_ready:
            self.trading_disabled = True
            self.trading_disabled_reason = "custom_data_path_missing"
            self.debug("CUSTOM_DATA_PATH_MISSING strategy=H0009 required=H0009_FUNDING_BTCUSDT_URL,H0009_FUNDING_ETHUSDT_URL")

        self.debug(
            "INIT H0009 "
            f"profile=B-Position tier=M zscore={FUNDING_EXTREME_ZSCORE:.2f} "
            f"hold_hours={HOLD_HOURS} per_trade_stop_frac={PER_TRADE_STOP_FRAC:.4f} "
            f"maker_fee_per_side={TIER_M_PER_SIDE_FEE:.4%} "
            f"adverse_threshold_bp={MAKER_DEFAULT_ADVERSE_THRESHOLD_BP:.1f} "
            f"custom_data_ready={self.custom_data_ready}"
        )

    def on_data(self, data):
        self._handle_day_rollover()
        self.daily_summary.on_equity(self.portfolio.total_portfolio_value)
        if self.drawdown_stop.update(self.portfolio.total_portfolio_value):
            self._trigger_project_drawdown_stop()
            return

        self._update_price_bars(data)
        self._resolve_maker_entries()
        self._check_position_exits()
        self._update_funding_events(data)
        self._check_custom_data_errors()

    def on_order_event(self, order_event):
        if order_event.status != OrderStatus.FILLED:
            if order_event.status == OrderStatus.INVALID or order_event.status == OrderStatus.CANCELED:
                self.debug(
                    "ORDER_EVENT "
                    f"timestamp={self.time} order_id={order_event.order_id} "
                    f"symbol={order_event.symbol} status={order_event.status}"
                )
            return

        context = self.order_context.get(order_event.order_id)
        if context is None:
            context = self.active_order_context
        if context is None:
            self.debug(
                "ORDER_EVENT_UNMATCHED "
                f"timestamp={self.time} order_id={order_event.order_id} "
                f"symbol={order_event.symbol} fill_price={order_event.fill_price}"
            )
            return

        state = self.states[context["trade_symbol"]]
        fill_price = float(order_event.fill_price)
        fill_quantity = float(order_event.fill_quantity)
        fee = abs(fill_quantity * fill_price * TIER_M_PER_SIDE_FEE)

        self.debug(
            "ORDER_EVENT "
            f"timestamp={self.time} order_id={order_event.order_id} symbol={state.ticker} "
            f"type={context['type']} fill_quantity={fill_quantity:.8f} "
            f"fill_price={fill_price:.8f} status={order_event.status}"
        )

        if context["type"] == "entry":
            self._mark_entry_filled(state, context, fill_price, fill_quantity, fee)
        else:
            self._mark_exit_filled(state, context, fill_price, fee)

    def on_end_of_algorithm(self):
        self._flatten_all("FINAL_LIQUIDATION")
        self.daily_summary.flush(self.time.date())

    def _configure_custom_data(self):
        H0009FundingRateData.parse_error_count = 0
        H0009FundingRateData.last_parse_error = ""
        required = {
            "H0009_FUNDING_BTCUSDT": self.get_parameter("H0009_FUNDING_BTCUSDT_URL"),
            "H0009_FUNDING_ETHUSDT": self.get_parameter("H0009_FUNDING_ETHUSDT_URL"),
        }
        ready = True
        for custom_symbol, url in required.items():
            if url is None or str(url).strip() == "":
                ready = False
            else:
                H0009FundingRateData.source_by_symbol[custom_symbol] = str(url).strip()
        return ready

    def _update_price_bars(self, data):
        for trade_symbol, state in self.states.items():
            if data.Bars.ContainsKey(trade_symbol):
                bar = data.Bars[trade_symbol]
                state.last_price_bar = bar
                self._count_holding_bar(state, bar)

    def _resolve_maker_entries(self):
        for trade_symbol, state in self.states.items():
            if state.position_open or state.entry_order_id is not None:
                self.maker_gate.cancel(trade_symbol)
                continue
            if state.last_price_bar is None:
                continue
            decision = self.maker_gate.resolve(trade_symbol, state.last_price_bar)
            if decision.action == "fill":
                context = decision.context
                if context is None:
                    continue
                context["type"] = "entry"
                quantity = decision.signed_quantity
                self.active_order_context = context
                ticket = self.market_order(trade_symbol, quantity, False, "H0009_MAKER_ENTRY_PROXY")
                self.order_context[ticket.order_id] = context
                state.entry_order_id = ticket.order_id
                self.active_order_context = None
                self.debug(
                    "ENTRY_ORDER_SUBMITTED "
                    f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                    f"quantity={quantity:.8f} limit_price={decision.fill_price:.8f} "
                    f"signal_bar_time={context['signal_bar_time']} funding_time={context['funding_time']} "
                    "reason_code=FUND_EXTREME_CONTINUATION"
                )
            elif decision.action == "expire":
                self.debug(
                    "MAKER_ENTRY_EXPIRED "
                    f"timestamp={self.time} symbol={state.ticker} "
                    "reason_code=TOUCHED_WITHOUT_ADVERSE_SELECTION"
                )

    def _update_funding_events(self, data):
        if self.trading_disabled:
            return
        for funding_symbol, trade_symbol in self.funding_to_trade_symbol.items():
            if not data.ContainsKey(funding_symbol):
                continue
            row = data[funding_symbol]
            state = self.states[trade_symbol]
            funding_time = row.EndTime
            funding_rate = float(row.Value)
            if state.last_funding_time is not None and funding_time <= state.last_funding_time:
                continue
            state.last_funding_time = funding_time
            side, zscore = self._fund_extreme_side(state, funding_rate)
            state.funding_history.append(funding_rate)
            if side == 0:
                state.no_signal_count += 1
                continue
            self._submit_signal(state, side, funding_time, funding_rate, zscore)

    def _fund_extreme_side(self, state, funding_rate):
        fallback_abs_rate = 5.0 / 10000.0
        zscore = 0.0
        side = 0
        if len(state.funding_history) >= 30:
            values = list(state.funding_history)
            mean = sum(values) / len(values)
            variance = sum((value - mean) * (value - mean) for value in values) / len(values)
            std = math.sqrt(variance)
            if std > 0.0:
                zscore = (funding_rate - mean) / std
                if zscore >= FUNDING_EXTREME_ZSCORE:
                    side = 1
                elif zscore <= -FUNDING_EXTREME_ZSCORE:
                    side = -1
        if side == 0 and abs(funding_rate) >= fallback_abs_rate:
            side = 1 if funding_rate > 0.0 else -1
        return side, zscore

    def _submit_signal(self, state, side, funding_time, funding_rate, zscore):
        if state.last_price_bar is None:
            self.debug(
                "SIGNAL_SKIPPED "
                f"timestamp={self.time} symbol={state.ticker} reason_code=MISSING_PRICE_BAR "
                f"funding_time={funding_time} funding_rate={funding_rate:.8f}"
            )
            return
        if state.position_open or self.portfolio[state.trade_symbol].invested:
            self.debug(
                "SIGNAL_SKIPPED "
                f"timestamp={self.time} symbol={state.ticker} reason_code=POSITION_ALREADY_OPEN "
                f"funding_time={funding_time} side={side}"
            )
            return
        if self.maker_gate.has_pending(state.trade_symbol):
            self.debug(
                "SIGNAL_SKIPPED "
                f"timestamp={self.time} symbol={state.ticker} reason_code=PENDING_MAKER_ENTRY "
                f"funding_time={funding_time} side={side}"
            )
            return

        limit_price = float(state.last_price_bar.close)
        quantity = self._position_quantity(state.trade_symbol, limit_price)
        if quantity <= 0.0:
            self.debug(
                "ORDER_SKIPPED_ZERO_QTY "
                f"timestamp={self.time} symbol={state.ticker} price={limit_price:.8f}"
            )
            return

        context = {
            "type": "entry",
            "trade_symbol": state.trade_symbol,
            "side": side,
            "signal_bar_time": state.last_price_bar.EndTime,
            "funding_time": funding_time,
            "funding_rate": funding_rate,
            "funding_zscore": zscore,
            "limit_price": limit_price,
        }
        self.maker_gate.submit(state.trade_symbol, side, limit_price, quantity, context)
        state.signals += 1
        self.debug(
            "SIGNAL "
            f"timestamp={self.time} symbol={state.ticker} side={side} "
            f"signal_bar_time={state.last_price_bar.EndTime} funding_time={funding_time} "
            f"funding_rate={funding_rate:.8f} funding_zscore={zscore:.4f} "
            f"limit_price={limit_price:.8f} quantity={quantity:.8f} "
            "reason_code=FUND_EXTREME_CONTINUATION"
        )

    def _position_quantity(self, symbol, price):
        if price <= 0.0:
            return 0.0
        notional = self.portfolio.total_portfolio_value
        raw_quantity = notional / price
        lot_size = float(self.securities[symbol].symbol_properties.lot_size)
        if lot_size <= 0.0:
            lot_size = 0.001
        rounded = math.floor(raw_quantity / lot_size) * lot_size
        return max(0.0, rounded)

    def _count_holding_bar(self, state, bar):
        if not state.position_open:
            return
        if state.entry_time is None:
            return
        if bar.EndTime <= state.entry_time:
            return
        if state.last_hold_bar_time == bar.EndTime:
            return
        state.bars_held += 1
        state.last_hold_bar_time = bar.EndTime

    def _check_position_exits(self):
        for trade_symbol, state in self.states.items():
            if not state.position_open:
                continue
            holding = self.portfolio[trade_symbol]
            price = float(self.securities[trade_symbol].price)
            if price <= 0.0:
                continue
            side = state.entry_side
            trade_return = side * (price - state.entry_price) / state.entry_price
            if trade_return <= -PER_TRADE_STOP_FRAC:
                self._submit_exit(state, "PER_TRADE_DRAWDOWN_STOP")
                continue
            if state.entry_time is not None and self.time >= state.entry_time + timedelta(hours=HOLD_HOURS):
                self._submit_exit(state, "TIME_EXIT_H72")
                continue
            if holding.quantity == 0:
                self._clear_position_state(state)

    def _submit_exit(self, state, reason_code):
        if state.exit_order_id is not None:
            return
        quantity = -float(self.portfolio[state.trade_symbol].quantity)
        if quantity == 0.0:
            return
        context = {
            "type": "exit",
            "trade_symbol": state.trade_symbol,
            "reason_code": reason_code,
        }
        self.active_order_context = context
        ticket = self.market_order(state.trade_symbol, quantity, False, "H0009_" + reason_code)
        self.order_context[ticket.order_id] = context
        state.exit_order_id = ticket.order_id
        self.active_order_context = None
        self.debug(
            "EXIT_ORDER_SUBMITTED "
            f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
            f"exit_qty={quantity:.8f} reason_code={reason_code} "
            f"entry_time={state.entry_time} bars_held={state.bars_held}"
        )

    def _mark_entry_filled(self, state, context, fill_price, fill_quantity, fee):
        state.position_open = True
        state.entry_time = self.time
        state.execution_time = self.time
        state.entry_price = fill_price
        state.entry_quantity = fill_quantity
        state.entry_fee = fee
        state.entry_side = int(context["side"])
        state.signal_time = context["signal_bar_time"]
        state.funding_time = context["funding_time"]
        state.funding_rate = float(context["funding_rate"])
        state.funding_zscore = float(context["funding_zscore"])
        state.entry_order_id = None
        state.exit_order_id = None
        state.bars_held = 0
        state.last_hold_bar_time = None
        delta_hours = (self.time - state.signal_time).total_seconds() / 3600.0
        self.debug(
            "ENTRY "
            f"timestamp={self.time} symbol={state.ticker} side={state.entry_side} "
            f"signal_bar_time={state.signal_time} execution_bar_time={self.time} "
            f"delta_hours={delta_hours:.2f} funding_time={state.funding_time} "
            f"funding_rate={state.funding_rate:.8f} funding_zscore={state.funding_zscore:.4f} "
            f"entry_price={fill_price:.8f} quantity={fill_quantity:.8f} "
            "reason_code=FUND_EXTREME_CONTINUATION"
        )

    def _mark_exit_filled(self, state, context, fill_price, exit_fee):
        if not state.position_open:
            return
        entry_notional = abs(state.entry_price * state.entry_quantity)
        gross_pnl = (fill_price - state.entry_price) * abs(state.entry_quantity) * state.entry_side
        pre_fee_pct = 0.0
        post_fee_pct = 0.0
        if entry_notional > 0.0:
            pre_fee_pct = 100.0 * gross_pnl / entry_notional
            post_fee_pct = 100.0 * (gross_pnl - state.entry_fee - exit_fee) / entry_notional
        delta_hours = 0.0
        if state.signal_time is not None and state.execution_time is not None:
            delta_hours = (state.execution_time - state.signal_time).total_seconds() / 3600.0
        self.trade_logger.record(
            timestamp=self.time,
            symbol=state.ticker,
            side=state.entry_side,
            entry_price=state.entry_price,
            exit_price=fill_price,
            holding_bars=state.bars_held,
            reason=context["reason_code"],
            pre_fee_pnl=pre_fee_pct,
            post_fee_pnl=post_fee_pct,
        )
        self.daily_summary.on_trade(pre_fee_pct, post_fee_pct)
        self.debug(
            "TRADE_DETAIL "
            f"timestamp={self.time} symbol={state.ticker} side={state.entry_side} "
            f"signal_bar_time={state.signal_time} execution_bar_time={state.execution_time} "
            f"delta_hours={delta_hours:.2f} funding_time={state.funding_time} "
            f"funding_rate={state.funding_rate:.8f} funding_zscore={state.funding_zscore:.4f} "
            f"entry_price={state.entry_price:.8f} exit_price={fill_price:.8f} "
            f"holding_bars={state.bars_held} reason_code={context['reason_code']} "
            f"pre_fee_pnl_pct={pre_fee_pct:.5f} post_fee_pnl_pct={post_fee_pct:.5f}"
        )
        self._clear_position_state(state)

    def _clear_position_state(self, state):
        state.entry_time = None
        state.entry_price = 0.0
        state.entry_quantity = 0.0
        state.entry_fee = 0.0
        state.entry_side = 0
        state.signal_time = None
        state.execution_time = None
        state.funding_time = None
        state.funding_rate = 0.0
        state.funding_zscore = 0.0
        state.bars_held = 0
        state.last_hold_bar_time = None
        state.entry_order_id = None
        state.exit_order_id = None
        state.position_open = False

    def _trigger_project_drawdown_stop(self):
        if self.trading_disabled and self.trading_disabled_reason == "project_drawdown_stop":
            return
        self.trading_disabled = True
        self.trading_disabled_reason = "project_drawdown_stop"
        self.debug(
            "PROJECT_STOP "
            f"timestamp={self.time} reason_code=PROJECT_DRAWDOWN_20PCT "
            f"portfolio_value={self.portfolio.total_portfolio_value:.2f}"
        )
        self._flatten_all("PROJECT_DRAWDOWN_20PCT")

    def _flatten_all(self, reason_code):
        for trade_symbol, state in self.states.items():
            self.maker_gate.cancel(trade_symbol)
            quantity = float(self.portfolio[trade_symbol].quantity)
            if quantity != 0.0:
                context = {
                    "type": "exit",
                    "trade_symbol": trade_symbol,
                    "reason_code": reason_code,
                }
                self.active_order_context = context
                ticket = self.market_order(trade_symbol, -quantity, False, "H0009_" + reason_code)
                self.order_context[ticket.order_id] = context
                state.exit_order_id = ticket.order_id
                self.active_order_context = None
                self.debug(
                    "EXIT_ORDER_SUBMITTED "
                    f"timestamp={self.time} symbol={state.ticker} order_id={ticket.order_id} "
                    f"exit_qty={-quantity:.8f} reason_code={reason_code}"
                )

    def _handle_day_rollover(self):
        today = self.time.date()
        if self.current_day is None:
            self.current_day = today
            return
        if today != self.current_day:
            self.daily_summary.flush(self.current_day)
            self.current_day = today

    def _check_custom_data_errors(self):
        if H0009FundingRateData.parse_error_count > 0:
            self.trading_disabled = True
            self.trading_disabled_reason = "custom_data_invalid"
            self.debug(
                "CUSTOM_DATA_INVALID "
                f"timestamp={self.time} parse_errors={H0009FundingRateData.parse_error_count} "
                f"last_error={H0009FundingRateData.last_parse_error}"
            )
            self._flatten_all("CUSTOM_DATA_INVALID")
