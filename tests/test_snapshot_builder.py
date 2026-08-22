"""Tests for snapshot-history serialization."""
import json
from datetime import date
from unittest.mock import patch

from stockmarket.data import Snapshot
from stockmarket.snapshot_builder import build_snapshot_history


def test_build_snapshot_history_writes_expected_shape(tmp_path):
    snapshot = Snapshot(
        "TEST", 100.0, 5.0, 5.5, 1_000_000, 100_000, 10_000,
        1.0, 20.0, 18.0, 0.2, 0.25, 0.3, 0.1, 0.1, 50.0, 1.5,
        1_000_000, "Technology"
    )
    output = tmp_path / "snapshots.json"

    with patch("stockmarket.snapshot_builder.fetch_snapshot",
               return_value=snapshot):
        build_snapshot_history("TEST", [date(2024, 1, 1)], output)

    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["ticker"] == "TEST"
    assert document["snapshots"]["2024-01-01"]["price"] == 100.0
    assert "point-in-time accuracy" in document["point_in_time_note"]