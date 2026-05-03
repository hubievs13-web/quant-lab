"""Phase 2 / 3 rebuild: align + join + (optionally) features + regimes."""
from __future__ import annotations

from pathlib import Path

from data_layer.process.align import aligned_bars
from data_layer.process.features import build_features_for
from data_layer.process.join import join_for
from data_layer.process.regimes import build_regimes_for

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
SYMBOL = "BTCUSDT"


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
    """Phase 3 convenience: align + join + features + regimes."""
    rebuild_smoke()
    for tf in ("5m", "1h"):
        print(f"[rebuild] features {SYMBOL} {tf}")
        fp, fn, _ = build_features_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {fp} rows={fn}")
        print(f"[rebuild] regimes {SYMBOL} {tf}")
        rp, rn = build_regimes_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {rp} rows={rn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild_smoke())
