"""Bar resampling / dedup (Phase 2).

Reads raw daily Parquet for OHLCV at native timeframe, dedupes on
`ts_open_ms` (keep first), sorts ascending, and writes the canonical
per-(symbol, timeframe) Parquet under `processed/bars/`.
"""
from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def aligned_bars(symbol: str, timeframe: str, store_root: Path) -> tuple[Path | None, int]:
    raw_dir = store_root / "raw/binance/ohlcv" / symbol / timeframe
    if not raw_dir.exists():
        return None, 0
    files = sorted(raw_dir.glob("*.parquet"))
    if not files:
        return None, 0
    table = pa.concat_tables([pq.read_table(p) for p in files])
    df = table.to_pandas()
    df = (
        df.drop_duplicates(subset=["ts_open_ms"], keep="first")
        .sort_values("ts_open_ms")
        .reset_index(drop=True)
    )
    out_table = pa.Table.from_pandas(df, preserve_index=False)
    out_path = store_root / "processed/bars/binance" / symbol / f"{timeframe}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(out_table, out_path, compression="snappy")
    return out_path, out_table.num_rows
