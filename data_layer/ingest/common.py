"""Common ingest helpers (Phase 2).

HTTP retry/backoff over urllib (stdlib), ZIP/CSV streaming, atomic
Parquet writes with sha256 sidecar checksums, tiny rate limiter,
and a couple of UTC time helpers. No `requests` dependency.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import random
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

USER_AGENT = "quant-lab-data-layer/0.2 (+https://github.com/hubievs13-web/quant-lab)"
DEFAULT_TIMEOUT_S = 15


class IngestError(RuntimeError):
    """Raised on permanent ingest failure (after retries)."""


def _sleep_backoff(attempt: int, initial: float = 0.5, factor: float = 2.0, jitter: float = 0.5) -> None:
    delay = initial * (factor ** attempt) + random.uniform(0, jitter)
    time.sleep(delay)


def http_get_bytes(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
    max_attempts: int = 5,
    accept_404_as_none: bool = False,
) -> bytes | None:
    """Fetch bytes with exponential backoff. 404 may be treated as missing."""
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status >= 400:
                    raise IngestError(f"HTTP {r.status} for {url}")
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 and accept_404_as_none:
                return None
            if 500 <= e.code < 600 or e.code == 429:
                last_err = e
                _sleep_backoff(attempt)
                continue
            raise IngestError(f"HTTP {e.code} for {url}: {e.reason}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            _sleep_backoff(attempt)
            continue
    raise IngestError(f"giving up on {url}: {last_err!r}")


def csv_rows_from_zip(payload: bytes) -> list[list[str]]:
    """Concatenate CSV rows across all files inside a ZIP payload."""
    rows: list[list[str]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for name in zf.namelist():
            with zf.open(name) as f:
                text = io.TextIOWrapper(f, encoding="utf-8")
                rows.extend(list(csv.reader(text)))
    return rows


def write_parquet_atomic(table: pa.Table, path: Path) -> str:
    """Atomic Parquet write + sha256 sidecar. Returns hex digest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    pq.write_table(table, tmp, compression="snappy")
    tmp.replace(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    side = path.with_suffix(path.suffix + ".checksum")
    side.write_text(f"sha256  {digest}  {path.name}\n")
    return digest


def utc_today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def daterange(start: dt.date, end_inclusive: dt.date) -> list[dt.date]:
    out: list[dt.date] = []
    cur = start
    while cur <= end_inclusive:
        out.append(cur)
        cur += dt.timedelta(days=1)
    return out


class RateLimiter:
    """Sleep-based requests-per-second limiter."""

    def __init__(self, rps: float) -> None:
        self._min_interval = 1.0 / max(rps, 0.001)
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last = time.monotonic()
