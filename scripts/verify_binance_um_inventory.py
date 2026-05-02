from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SYMBOLS = ("BTCUSDT", "ETHUSDT")
OUT_DIR = Path("data_inventory")

UTC = timezone.utc
MS_2021_01_01 = 1609459200000
MS_2024_01_01 = 1704067200000
MS_2024_01_01_PLUS_1H = 1704070800000 - 1
MS_2024_01_01_PLUS_1D = 1704153600000 - 1
MS_2024_02_01 = 1706745600000 - 1


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    source_type: str
    endpoint_template: str
    expected_schema_fields: list[str]
    rest_base: str | None
    archive_template: str | None
    interval_ms: int | None
    expected_interval: str
    old_params: dict[str, Any]
    sample_params: dict[str, Any]
    recent_params: dict[str, Any]
    candidate_hypotheses: str
    docs_limit_note: str
    check_archive_2021: bool = False


def ms_to_iso(ms: int | None) -> str:
    if ms is None:
        return ""
    return datetime.fromtimestamp(ms / 1000, UTC).isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def build_url(base: str, params: dict[str, Any]) -> str:
    return f"{base}?{urlencode(params)}"


def fetch_url(url: str, *, method: str = "GET", max_bytes: int = 2_000_000) -> tuple[int, bytes, str]:
    req = Request(url, method=method, headers={"User-Agent": "quant-lab-inventory/1.0"})
    try:
        with urlopen(req, timeout=2.5) as response:
            if method == "HEAD":
                return response.status, b"", ""
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                return response.status, body[:max_bytes], "TRUNCATED"
            return response.status, body, ""
    except HTTPError as exc:
        body = b""
        try:
            body = exc.read(4096)
        except Exception:
            pass
        return exc.code, body, f"HTTPError: {exc.reason}"
    except URLError as exc:
        return 0, b"", f"URLError: {exc.reason}"
    except Exception as exc:
        return 0, b"", f"{type(exc).__name__}: {exc}"


def parse_json_rows(body: bytes) -> list[Any]:
    if not body:
        return []
    payload = json.loads(body.decode("utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "code" in payload and "msg" in payload:
        return []
    return [payload]


def row_timestamp(dataset_id: str, row: Any) -> int | None:
    if isinstance(row, list) and row:
        try:
            return int(row[0])
        except Exception:
            return None
    if isinstance(row, dict):
        for key in ("fundingTime", "timestamp", "time", "T"):
            if key in row:
                try:
                    return int(row[key])
                except Exception:
                    return None
        if dataset_id == "um_agg_trades" and "T" in row:
            return int(row["T"])
    return None


def observed_fields(row: Any) -> str:
    if isinstance(row, list):
        return ",".join(f"col{i}" for i in range(len(row)))
    if isinstance(row, dict):
        return ",".join(row.keys())
    return type(row).__name__


def count_duplicates(timestamps: list[int]) -> int:
    return len(timestamps) - len(set(timestamps))


def gap_stats(timestamps: list[int], interval_ms: int | None) -> tuple[int, bool, int]:
    if not timestamps:
        return 0, True, 0
    monotonic = all(a <= b for a, b in zip(timestamps, timestamps[1:]))
    duplicates = count_duplicates(timestamps)
    if interval_ms is None:
        return 0, monotonic, duplicates
    unique_sorted = sorted(set(timestamps))
    missing = 0
    for prev, curr in zip(unique_sorted, unique_sorted[1:]):
        gap = curr - prev
        if gap > interval_ms:
            missing += max(0, (gap // interval_ms) - 1)
    return missing, monotonic, duplicates


def expected_rows_for_window(start_ms: int, end_ms: int, interval_ms: int | None) -> str:
    if interval_ms is None:
        return ""
    return str(((end_ms - start_ms) // interval_ms) + 1)


def archive_url(template: str, symbol: str, year: int, month: int, day: int = 1) -> str:
    return template.format(SYMBOL=symbol, YYYY=f"{year:04d}", MM=f"{month:02d}", DD=f"{day:02d}", PAIR=symbol)


def classify(dataset: Dataset, sample_rows: int, recent_rows: int, old_rows: int, archive_2021: str) -> tuple[str, str, str]:
    old_available = old_rows > 0 or archive_2021 == "YES"
    if dataset.dataset_id in {"open_interest_statistics", "taker_buy_sell_volume", "basis"}:
        if old_rows > 0:
            return "YES", "TIER 1", "Unexpected old REST data observed; verify deeply before relying on docs-limit assumption."
        if recent_rows > 0:
            return "NO", "TIER 2", dataset.docs_limit_note
        return "UNKNOWN", "UNKNOWN", "Recent sample unavailable; cannot verify."
    if dataset.dataset_id in {"um_agg_trades", "um_trades"}:
        if old_available and recent_rows > 0:
            return "UNKNOWN", "UNKNOWN", "Availability observed, but raw trade history is heavy; not approved as TIER 1 ingestion."
        return "UNKNOWN", "UNKNOWN", "Trade archive or recent sample not fully verified."
    if old_available and recent_rows > 0:
        return "YES", "TIER 1", "Free source appears to support 12+ month research from small samples/archive existence."
    if recent_rows > 0:
        return "UNKNOWN", "UNKNOWN", "Recent sample works, but old history/archive was not verified."
    return "UNKNOWN", "UNKNOWN", "No reliable sample observed."


def make_datasets() -> list[Dataset]:
    kline_fields = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trade_count",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]
    price_kline_fields = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "ignore_1",
        "close_time",
        "ignore_2",
        "ignore_3",
        "ignore_4",
        "ignore_5",
        "ignore_6",
    ]
    return [
        Dataset(
            "um_klines_1m",
            "REST+archive",
            "https://fapi.binance.com/fapi/v1/klines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500",
            kline_fields,
            "https://fapi.binance.com/fapi/v1/klines",
            "https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            60_000,
            "1m",
            {"interval": "1m", "startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 3_600_000 - 1, "limit": 60},
            {"interval": "1m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1H, "limit": 60},
            {"interval": "1m", "limit": 60},
            "all Tier 1 price/reference candidates",
            "",
            True,
        ),
        Dataset(
            "funding_rate_history",
            "REST",
            "https://fapi.binance.com/fapi/v1/fundingRate?symbol={SYMBOL}&startTime={START_MS}&endTime={END_MS}&limit=1000",
            ["symbol", "fundingRate", "fundingTime", "markPrice"],
            "https://fapi.binance.com/fapi/v1/fundingRate",
            "https://data.binance.vision/data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY}-{MM}.zip",
            28_800_000,
            "8h_expected",
            {"startTime": MS_2021_01_01, "endTime": MS_2024_02_01, "limit": 5},
            {"startTime": MS_2024_01_01, "endTime": MS_2024_02_01, "limit": 100},
            {"limit": 20},
            "CE0016; funding regime with premium confirmation",
            "",
            True,
        ),
        Dataset(
            "premium_index_klines",
            "REST+archive",
            "https://fapi.binance.com/fapi/v1/premiumIndexKlines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500",
            price_kline_fields,
            "https://fapi.binance.com/fapi/v1/premiumIndexKlines",
            "https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            60_000,
            "1m",
            {"interval": "1m", "startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 3_600_000 - 1, "limit": 60},
            {"interval": "1m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1H, "limit": 60},
            {"interval": "1m", "limit": 60},
            "CE0016; premium compression repricing",
            "",
            True,
        ),
        Dataset(
            "mark_price_klines",
            "REST+archive",
            "https://fapi.binance.com/fapi/v1/markPriceKlines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500",
            price_kline_fields,
            "https://fapi.binance.com/fapi/v1/markPriceKlines",
            "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            60_000,
            "1m",
            {"interval": "1m", "startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 3_600_000 - 1, "limit": 60},
            {"interval": "1m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1H, "limit": 60},
            {"interval": "1m", "limit": 60},
            "CE0018",
            "",
            True,
        ),
        Dataset(
            "index_price_klines",
            "REST+archive",
            "https://fapi.binance.com/fapi/v1/indexPriceKlines?pair={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1500",
            price_kline_fields,
            "https://fapi.binance.com/fapi/v1/indexPriceKlines",
            "https://data.binance.vision/data/futures/um/monthly/indexPriceKlines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            60_000,
            "1m",
            {"interval": "1m", "startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 3_600_000 - 1, "limit": 60},
            {"interval": "1m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1H, "limit": 60},
            {"interval": "1m", "limit": 60},
            "CE0018; derived basis/premium models",
            "",
            True,
        ),
        Dataset(
            "open_interest_statistics",
            "REST",
            "https://fapi.binance.com/futures/data/openInterestHist?symbol={SYMBOL}&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500",
            ["symbol", "sumOpenInterest", "sumOpenInterestValue", "CMCCirculatingSupply", "timestamp"],
            "https://fapi.binance.com/futures/data/openInterestHist",
            None,
            300_000,
            "5m",
            {"period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 10},
            {"period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 288},
            {"period": "5m", "limit": 288},
            "CE0017",
            "Binance docs state only latest 1 month is available; treat as recent/forward collection unless old REST returns data.",
        ),
        Dataset(
            "taker_buy_sell_volume",
            "REST",
            "https://fapi.binance.com/futures/data/takerlongshortRatio?symbol={SYMBOL}&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500",
            ["buySellRatio", "buyVol", "sellVol", "timestamp"],
            "https://fapi.binance.com/futures/data/takerlongshortRatio",
            None,
            300_000,
            "5m",
            {"period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 10},
            {"period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 288},
            {"period": "5m", "limit": 288},
            "CE0019",
            "Binance docs state only latest 30 days is available; treat as recent/forward collection unless old REST returns data.",
        ),
        Dataset(
            "basis",
            "REST",
            "https://fapi.binance.com/futures/data/basis?pair={SYMBOL}&contractType=PERPETUAL&period=5m&startTime={START_MS}&endTime={END_MS}&limit=500",
            ["indexPrice", "contractType", "basisRate", "futuresPrice", "annualizedBasisRate", "basis", "pair", "timestamp"],
            "https://fapi.binance.com/futures/data/basis",
            None,
            300_000,
            "5m",
            {"contractType": "PERPETUAL", "period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 10},
            {"contractType": "PERPETUAL", "period": "5m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1D, "limit": 288},
            {"contractType": "PERPETUAL", "period": "5m", "limit": 288},
            "basis/premium dislocation candidates",
            "Binance docs state only latest 30 days is available; exchange basis endpoint is recent-only unless old REST returns data.",
        ),
        Dataset(
            "spot_klines_1m_optional",
            "REST+archive",
            "https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval=1m&startTime={START_MS}&endTime={END_MS}&limit=1000",
            kline_fields,
            "https://api.binance.com/api/v3/klines",
            "https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY}-{MM}.zip",
            60_000,
            "1m",
            {"interval": "1m", "startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 3_600_000 - 1, "limit": 60},
            {"interval": "1m", "startTime": MS_2024_01_01, "endTime": MS_2024_01_01_PLUS_1H, "limit": 60},
            {"interval": "1m", "limit": 60},
            "optional basis proxy",
            "Spot timestamps may use microseconds in public archive from 2025 onward; normalize if ingested.",
            True,
        ),
        Dataset(
            "um_agg_trades",
            "REST+archive",
            "https://fapi.binance.com/fapi/v1/aggTrades?symbol={SYMBOL}&startTime={START_MS}&endTime={END_MS}&limit=1000",
            ["aggregate_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "timestamp", "isBuyerMaker"],
            "https://fapi.binance.com/fapi/v1/aggTrades",
            "https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{YYYY}-{MM}-{DD}.zip",
            None,
            "tick_aggregate",
            {"startTime": MS_2021_01_01, "endTime": MS_2021_01_01 + 600_000 - 1, "limit": 100},
            {"startTime": MS_2024_01_01, "endTime": MS_2024_01_01 + 600_000 - 1, "limit": 100},
            {"limit": 100},
            "CE0019 if signed-flow reconstruction is approved",
            "Availability check only; raw aggTrades are not approved for full ingestion in this task.",
            True,
        ),
    ]


def symbol_params(dataset: Dataset, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    out = dict(params)
    if dataset.dataset_id in {"index_price_klines", "basis"}:
        out["pair"] = symbol
    else:
        out["symbol"] = symbol
    return out


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    inventory_rows: list[dict[str, Any]] = []
    gaps_rows: list[dict[str, Any]] = []
    checksum_rows: list[dict[str, Any]] = []
    checked_at = now_iso()

    for dataset in make_datasets():
        for symbol in SYMBOLS:
            if dataset.rest_base is None:
                continue

            sample_url = build_url(dataset.rest_base, symbol_params(dataset, symbol, dataset.sample_params))
            recent_url = build_url(dataset.rest_base, symbol_params(dataset, symbol, dataset.recent_params))
            old_url = build_url(dataset.rest_base, symbol_params(dataset, symbol, dataset.old_params))

            status, body, err = fetch_url(sample_url)
            time.sleep(0.08)
            recent_status, recent_body, recent_err = fetch_url(recent_url)
            time.sleep(0.08)
            old_status, old_body, old_err = fetch_url(old_url)
            time.sleep(0.08)

            rows: list[Any] = []
            recent_rows: list[Any] = []
            old_rows: list[Any] = []
            parse_err = ""
            if status == 200:
                try:
                    rows = parse_json_rows(body)
                except Exception as exc:
                    parse_err = f"sample parse error: {exc}"
            if recent_status == 200:
                try:
                    recent_rows = parse_json_rows(recent_body)
                except Exception as exc:
                    recent_err = f"{recent_err}; recent parse error: {exc}".strip("; ")
            if old_status == 200:
                try:
                    old_rows = parse_json_rows(old_body)
                except Exception as exc:
                    old_err = f"{old_err}; old parse error: {exc}".strip("; ")

            archive_2021 = ""
            archive_url_2021 = ""
            if dataset.check_archive_2021 and dataset.archive_template:
                archive_url_2021 = archive_url(dataset.archive_template, symbol, 2021, 1, 1)
                head_status, head_body, head_err = fetch_url(archive_url_2021, method="HEAD")
                if head_status == 200:
                    archive_2021 = "YES"
                elif head_status in {403, 405, 0}:
                    # Small ranged GET is still metadata verification. It does not download the zip.
                    req = Request(archive_url_2021, headers={"Range": "bytes=0-0", "User-Agent": "quant-lab-inventory/1.0"})
                    try:
                        with urlopen(req, timeout=2.5) as response:
                            archive_2021 = "YES" if response.status in {200, 206} else "NO"
                    except HTTPError as exc:
                        archive_2021 = "NO" if exc.code == 404 else f"UNKNOWN_HTTP_{exc.code}"
                    except Exception:
                        archive_2021 = "UNKNOWN"
                else:
                    archive_2021 = "NO" if head_status == 404 else f"UNKNOWN_HTTP_{head_status}"
                time.sleep(0.08)

            timestamps = [ts for ts in (row_timestamp(dataset.dataset_id, row) for row in rows) if ts is not None]
            recent_timestamps = [ts for ts in (row_timestamp(dataset.dataset_id, row) for row in recent_rows) if ts is not None]
            old_timestamps = [ts for ts in (row_timestamp(dataset.dataset_id, row) for row in old_rows) if ts is not None]

            observed_oldest_candidates = []
            if old_timestamps:
                observed_oldest_candidates.append(min(old_timestamps))
            if archive_2021 == "YES":
                observed_oldest_candidates.append(MS_2021_01_01)

            latest_candidates = []
            if recent_timestamps:
                latest_candidates.append(max(recent_timestamps))
            if timestamps:
                latest_candidates.append(max(timestamps))

            enough_12m, tier, class_note = classify(dataset, len(rows), len(recent_rows), len(old_rows), archive_2021)
            notes = []
            if err:
                notes.append(err)
            if parse_err:
                notes.append(parse_err)
            if old_err:
                notes.append(f"old_check={old_err}")
            if recent_err:
                notes.append(f"recent_check={recent_err}")
            if archive_2021:
                notes.append(f"archive_2021={archive_2021}")
            if class_note:
                notes.append(class_note)

            inventory_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "source_type": dataset.source_type,
                    "endpoint_or_archive_template": dataset.archive_template or dataset.endpoint_template,
                    "sample_url": sample_url,
                    "sample_status": str(status),
                    "sample_rows": len(rows),
                    "first_timestamp_checked": ms_to_iso(MS_2021_01_01),
                    "oldest_available_timestamp_observed": ms_to_iso(min(observed_oldest_candidates) if observed_oldest_candidates else None),
                    "latest_available_timestamp_observed": ms_to_iso(max(latest_candidates) if latest_candidates else None),
                    "expected_schema_fields": ",".join(dataset.expected_schema_fields),
                    "observed_schema_fields": observed_fields(rows[0]) if rows else "",
                    "enough_for_12m_research": enough_12m,
                    "tier": tier,
                    "notes": " | ".join(notes),
                }
            )

            missing, monotonic, duplicates = gap_stats(timestamps, dataset.interval_ms)
            check_start = min(timestamps) if timestamps else None
            check_end = max(timestamps) if timestamps else None
            expected_rows = expected_rows_for_window(check_start, check_end, dataset.interval_ms) if check_start and check_end else ""
            gaps_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "check_window_start": ms_to_iso(check_start),
                    "check_window_end": ms_to_iso(check_end),
                    "expected_interval": dataset.expected_interval,
                    "expected_rows": expected_rows,
                    "observed_rows": len(rows),
                    "missing_rows": missing,
                    "duplicate_rows": duplicates,
                    "timestamp_monotonic": str(monotonic).upper(),
                    "status": "OK" if rows and missing == 0 and duplicates == 0 and monotonic else ("NO_SAMPLE" if not rows else "CHECK"),
                    "notes": "Small sample only; not a full historical gap audit.",
                }
            )

            response_id = f"{dataset.dataset_id}_{symbol}_sample_2024"
            checksum_rows.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "symbol": symbol,
                    "sample_file_or_response_id": response_id,
                    "source_url": sample_url,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest() if body else "",
                    "checked_at_utc": checked_at,
                    "notes": "REST sample response checksum; no full historical file downloaded.",
                }
            )
            if archive_url_2021:
                checksum_rows.append(
                    {
                        "dataset_id": dataset.dataset_id,
                        "symbol": symbol,
                        "sample_file_or_response_id": f"{dataset.dataset_id}_{symbol}_archive_2021_01_head",
                        "source_url": archive_url_2021,
                        "bytes": 0,
                        "sha256": "",
                        "checked_at_utc": checked_at,
                        "notes": f"Archive existence check only: {archive_2021}. Zip was not downloaded.",
                    }
                )

    write_csv(
        OUT_DIR / "source_inventory.csv",
        [
            "dataset_id",
            "symbol",
            "source_type",
            "endpoint_or_archive_template",
            "sample_url",
            "sample_status",
            "sample_rows",
            "first_timestamp_checked",
            "oldest_available_timestamp_observed",
            "latest_available_timestamp_observed",
            "expected_schema_fields",
            "observed_schema_fields",
            "enough_for_12m_research",
            "tier",
            "notes",
        ],
        inventory_rows,
    )
    write_csv(
        OUT_DIR / "gaps_report.csv",
        [
            "dataset_id",
            "symbol",
            "check_window_start",
            "check_window_end",
            "expected_interval",
            "expected_rows",
            "observed_rows",
            "missing_rows",
            "duplicate_rows",
            "timestamp_monotonic",
            "status",
            "notes",
        ],
        gaps_rows,
    )
    write_csv(
        OUT_DIR / "checksums.csv",
        [
            "dataset_id",
            "symbol",
            "sample_file_or_response_id",
            "source_url",
            "bytes",
            "sha256",
            "checked_at_utc",
            "notes",
        ],
        checksum_rows,
    )

    tier_counts: dict[str, int] = {}
    for row in inventory_rows:
        tier_counts[row["tier"]] = tier_counts.get(row["tier"], 0) + 1
    print("Inventory verification complete.")
    print(f"Wrote {OUT_DIR / 'source_inventory.csv'}")
    print(f"Wrote {OUT_DIR / 'gaps_report.csv'}")
    print(f"Wrote {OUT_DIR / 'checksums.csv'}")
    print("Tier counts:", json.dumps(tier_counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
