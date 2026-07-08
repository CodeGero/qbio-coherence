"""Persistent coherence leaderboard: accumulate falsification verdicts as JSON.

The leaderboard is the public asset — a growing, machine-checkable registry of
biological quantum-coherence claims with verdicts, citations, and failure modes.
It is what labs cite and what the agentic layer appends to on every run.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from .claims import claim_from_dict, Claim
from .falsify import falsify, report_to_row


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "leaderboard.json")


def load_board(path: str = DEFAULT_PATH) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"created": _now_iso(), "entries": []}


def save_board(board: dict, path: str = DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(board, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_claim(
    claim: Claim,
    path: str = DEFAULT_PATH,
    source_tag: str = "manual",
) -> dict:
    """Run falsify on a claim and append the verdict row to the leaderboard."""
    board = load_board(path)
    row = report_to_row(falsify(claim))
    row["added"] = _now_iso()
    row["source_tag"] = source_tag
    # de-dup by claim name + verdict + mechanism
    for e in board["entries"]:
        if (
            e["claim"] == row["claim"]
            and e["verdict"] == row["verdict"]
            and e["mechanism"] == row["mechanism"]
        ):
            e.update(row)  # refresh timestamp/source
            save_board(board, path)
            return e
    board["entries"].append(row)
    save_board(board, path)
    return row


def add_from_dict(d: dict, path: str = DEFAULT_PATH, source_tag: str = "manual") -> dict:
    return add_claim(claim_from_dict(d), path=path, source_tag=source_tag)


def summarize(path: str = DEFAULT_PATH) -> dict:
    board = load_board(path)
    counts = {"SURVIVES": 0, "FALSIFIED": 0, "UNTESTED": 0}
    for e in board["entries"]:
        counts[e["verdict"]] = counts.get(e["verdict"], 0) + 1
    return {
        "total": len(board["entries"]),
        "verdicts": counts,
        "baseline": "Firmenich 2026 HEOM, gamma=7.69e13 Hz, tau_coh=13 fs @310K",
        "created": board.get("created"),
    }
