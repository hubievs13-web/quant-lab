"""Phase 2 / 3 rebuild: align + join + (optionally) features + regimes."""
from __future__ import annotations

from pathlib import Path

from data_layer.process.align import aligned_bars
from data_layer.process.events import detect_events_for
from data_layer.process.features import build_features_for
from data_layer.process.join import join_for
from data_layer.process.leaderboard import build_leaderboard_for
from data_layer.process.outcomes import build_outcomes_for
from data_layer.process.regimes import build_regimes_for

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
SYMBOL = "BTCUSDT"
SYMBOLS = ("BTCUSDT", "ETHUSDT")


def rebuild_smoke() -> int:
    """Phase 2 smoke: align + join only (no features/regimes)."""
    for tf in ("5m", "1h"):
        print(f"[rebuild] align {SYMBOL} {tf}")
        path, n = aligned_bars(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {path} rows={n}")
        print(f"[rebuild] join {SYMBOL} {tf}")
        path2, n2 = join_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {path2} rows={n2}")
    print("[rebuild] done.")
    return 0


def rebuild_smoke_full() -> int:
    """Phase 2/3/4 convenience: align + join + features + regimes + events + outcomes + leaderboard."""
    rebuild_smoke()
    for tf in ("5m", "1h"):
        print(f"[rebuild] features {SYMBOL} {tf}")
        fp, fn, _ = build_features_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {fp} rows={fn}")
        print(f"[rebuild] regimes {SYMBOL} {tf}")
        rp, rn = build_regimes_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {rp} rows={rn}")
        print(f"[rebuild] events {SYMBOL} {tf}")
        ep, en, _ = detect_events_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {ep} rows={en}")
        print(f"[rebuild] outcomes {SYMBOL} {tf}")
        op, on = build_outcomes_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {op} rows={on}")
        print(f"[rebuild] leaderboard {SYMBOL} {tf}")
        lp, ln = build_leaderboard_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {lp} rows={ln}")
    return 0


def rebuild_validation(symbols: tuple[str, ...] = SYMBOLS) -> int:
    """Full rebuild for Binance BTCUSDT / ETHUSDT validation."""
    for symbol in symbols:
        for tf in ("5m", "1h"):
            print(f"[rebuild] align {symbol} {tf}")
            path, n = aligned_bars(symbol, tf, STORE_ROOT)
            print(f"  -> {path} rows={n}")
            print(f"[rebuild] join {symbol} {tf}")
            path2, n2 = join_for(symbol, tf, STORE_ROOT)
            print(f"  -> {path2} rows={n2}")
            print(f"[rebuild] features {symbol} {tf}")
            fp, fn, _ = build_features_for(symbol, tf, STORE_ROOT)
            print(f"  -> {fp} rows={fn}")
            print(f"[rebuild] regimes {symbol} {tf}")
            rp, rn = build_regimes_for(symbol, tf, STORE_ROOT)
            print(f"  -> {rp} rows={rn}")
            print(f"[rebuild] events {symbol} {tf}")
            ep, en, _ = detect_events_for(symbol, tf, STORE_ROOT)
            print(f"  -> {ep} rows={en}")
            print(f"[rebuild] outcomes {symbol} {tf}")
            op, on = build_outcomes_for(symbol, tf, STORE_ROOT)
            print(f"  -> {op} rows={on}")
            print(f"[rebuild] leaderboard {symbol} {tf}")
            lp, ln = build_leaderboard_for(symbol, tf, STORE_ROOT)
            print(f"  -> {lp} rows={ln}")
    print("[rebuild] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild_smoke())
