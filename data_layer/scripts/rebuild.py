"""Phase 2 rebuild: align + join from local raw/."""
from __future__ import annotations

from pathlib import Path

from data_layer.process.align import aligned_bars
from data_layer.process.join import join_for

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_ROOT = REPO_ROOT / "data_layer" / "store"
SYMBOL = "BTCUSDT"


def rebuild_smoke() -> int:
    for tf in ("5m", "1h"):
        print(f"[rebuild] align {SYMBOL} {tf}")
        path, n = aligned_bars(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {path} rows={n}")
        print(f"[rebuild] join {SYMBOL} {tf}")
        path2, n2 = join_for(SYMBOL, tf, STORE_ROOT)
        print(f"  -> {path2} rows={n2}")
    print("[rebuild] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild_smoke())
