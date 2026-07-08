"""NULLIUS ledger: append-only, tamper-evident verdict store.

The ledger is the permanence layer of the Bio-Coherence Falsifier. Every
falsification verdict is recorded as a hash-chained entry so that the scientific
record is auditable and tamper-evident: altering any past verdict breaks the
chain from that point forward, and the break is detectable by `verify()`.

This is "Nullius in verba" made operational -- a permanent, physics-anchored
public record of which biological quantum-coherence claims survive the Firmenich
dephasing floor and which do not.

Design:
  - chain.jsonl : one canonical JSON object per line, in append order.
  - root.json    : head hash + head sequence + timestamp of the latest entry.
  - entry_hash   : sha256(prev_head_hash || canonical(payload))
  - head_hash    : sha256(canonical(line))  (stored in root.json)

Integrity check recomputes every entry_hash and prev_hash link from scratch and
reports the first broken index, or valid=True with the count.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

DEFAULT_LEDGER_DIR = os.path.join(os.path.dirname(__file__), "..", "nullius_ledger")


def _canon(obj) -> str:
    """Deterministic canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LedgerEntry:
    """A single tamper-evident ledger entry (in-memory view)."""

    def __init__(self, seq, timestamp, prev_hash, entry_hash, payload):
        self.seq = seq
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.entry_hash = entry_hash
        self.payload = payload

    def as_dict(self) -> dict:
        return {
            "seq": self.seq,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
            "payload": self.payload,
        }

    def to_line(self) -> str:
        return _canon(self.as_dict())


class Ledger:
    """Append-only hash-chained verdict ledger."""

    def __init__(self, path: str = None):
        self.path = os.path.abspath(path or DEFAULT_LEDGER_DIR)
        self.chain_file = os.path.join(self.path, "chain.jsonl")
        self.root_file = os.path.join(self.path, "root.json")
        os.makedirs(self.path, exist_ok=True)

    # --- internal helpers ---------------------------------------------------
    def _count(self) -> int:
        if not os.path.exists(self.chain_file):
            return 0
        with open(self.chain_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def _read_raw(self) -> list:
        if not os.path.exists(self.chain_file):
            return []
        out = []
        with open(self.chain_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
        return out

    def _head_hash(self) -> str:
        if os.path.exists(self.root_file):
            with open(self.root_file, "r", encoding="utf-8") as f:
                return json.load(f).get("head_hash", "")
        return ""

    # --- public API ---------------------------------------------------------
    def add(self, payload: dict) -> LedgerEntry:
        """Append a verdict payload; returns the created entry.

        `payload` should be a JSON-serializable dict (e.g. a leaderboard row
        produced by report_to_row). Determinism: the canonical form is used so
        the same payload always hashes identically.
        """
        prev = self._head_hash()
        seq = self._count()
        ts = _now_iso()
        entry_hash = _sha(prev + "|" + _canon(payload))
        entry = LedgerEntry(seq, ts, prev, entry_hash, payload)
        line = entry.to_line()
        with open(self.chain_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        with open(self.root_file, "w", encoding="utf-8") as f:
            # The recorded head_hash is THIS entry's entry_hash, which is exactly
            # what the next entry will use as its prev_hash link.
            json.dump(
                {"head_hash": entry_hash, "head_seq": seq, "updated": ts},
                f,
                indent=2,
            )
        return entry

    def commit_rows(self, rows: list, reset: bool = False) -> int:
        """Commit a list of verdict rows (e.g. from the leaderboard).

        If reset=True, the chain is cleared first (dev/reproducibility only --
        a production ledger should never be reset). Returns the number of
        entries appended.
        """
        if reset:
            self.reset()
        n = 0
        for row in rows:
            # Store only the stable verdict fields, drop volatile bookkeeping.
            payload = {k: row[k] for k in row if k not in ("added", "source_tag")}
            self.add(payload)
            n += 1
        return n

    def reset(self) -> None:
        """DANGER: clears the chain. Production ledgers must not call this."""
        if os.path.exists(self.chain_file):
            os.remove(self.chain_file)
        if os.path.exists(self.root_file):
            os.remove(self.root_file)

    def entries(self) -> list:
        return [LedgerEntry(e["seq"], e["timestamp"], e["prev_hash"],
                            e["entry_hash"], e["payload"]) for e in self._read_raw()]

    def verify(self) -> dict:
        """Recompute the full chain from scratch.

        Returns {"valid": True, "count": N} on success, or
        {"valid": False, "broken_at": i, "reason": str} on the first break.
        """
        raw = self._read_raw()
        prev = ""
        seq = 0
        for i, line in enumerate(raw):
            recomputed = _sha(prev + "|" + _canon(line["payload"]))
            if recomputed != line["entry_hash"]:
                return {"valid": False, "broken_at": i,
                        "reason": "entry_hash mismatch (payload altered)"}
            if line["prev_hash"] != prev:
                return {"valid": False, "broken_at": i,
                        "reason": "prev_hash link broken (prior entry altered)"}
            if line["seq"] != seq:
                return {"valid": False, "broken_at": i,
                        "reason": f"sequence gap (expected {seq}, got {line['seq']})"}
            prev = line["entry_hash"]  # correct rolling link for the next entry
            seq += 1
        # Cross-check the recorded head hash matches the last entry's entry_hash.
        if raw:
            recorded = self._head_hash()
            if recorded and recorded != raw[-1]["entry_hash"]:
                return {"valid": False, "broken_at": len(raw) - 1,
                        "reason": "root head_hash does not match last entry"}
        return {"valid": True, "count": seq}


def commit_leaderboard(leaderboard_path: str, ledger_dir: str = None,
                       reset: bool = False) -> int:
    """Convenience: commit all current leaderboard entries into the ledger."""
    from .leaderboard import load_board

    board = load_board(leaderboard_path)
    ledger = Ledger(ledger_dir)
    return ledger.commit_rows(board["entries"], reset=reset)
