"""Build JSON financial snapshots for reproducible research runs."""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

from .data import fetch_snapshot


def build_snapshot_history(
    ticker: str, dates: Iterable[date | datetime | str], out_path: str | Path
) -> Path:
    """Write snapshots keyed by date.

    yfinance exposes current and trailing fundamentals rather than a complete
    point-in-time history. This builder therefore records the best available
    snapshot for each requested date and labels the resulting file as an
    approximation; it must not be interpreted as institutional-grade
    point-in-time data.
    """
    snapshot = fetch_snapshot(ticker)
    payload = {}
    for value in dates:
        if isinstance(value, datetime):
            key = value.date().isoformat()
        elif isinstance(value, date):
            key = value.isoformat()
        else:
            key = str(value)
        payload[key] = snapshot.to_dict()

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "ticker": ticker,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "point_in_time_note": (
            "Fundamentals are the best available current yfinance snapshot, "
            "repeated for requested dates; historical point-in-time accuracy "
            "is not guaranteed."
        ),
        "snapshots": payload,
    }
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path
