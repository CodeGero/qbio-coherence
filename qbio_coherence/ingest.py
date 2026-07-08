"""Agentic ingestion driver for the Bio-Coherence Falsifier.

This is the headless entry point the weekly cron runs. It takes a list of
extracted coherence CLAIMS (as dicts) and appends each verdict to the
leaderboard. The CLAIM EXTRACTION (reading a paper, pulling the claimed tau /
temperature / system / mechanism) is the agent's job; this script is the
deterministic, physics-enforced verdict stage.

Usage:
    python -m qbio_coherence.ingest --self-test
    python -m qbio_coherence.ingest --claims claims.json --path leaderboard.json
"""

import argparse
import json
import sys

from .claims import claim_from_dict
from .leaderboard import add_from_dict, summarize, load_board


def ingest_claims(claims: list[dict], path: str, source_tag: str = "agent") -> list[dict]:
    rows = []
    for c in claims:
        rows.append(add_from_dict(c, path=path, source_tag=source_tag))
    return rows


def self_test(path: str) -> None:
    """Seed the leaderboard with the built-in claim library (verifiable baseline)."""
    from .claims import BUILTIN_CLAIMS

    rows = []
    for c in BUILTIN_CLAIMS:
        rows.append(add_from_dict(c.to_dict(), path=path, source_tag="builtin"))
    s = summarize(path)
    print(f"[self-test] seeded {s['total']} claims -> {s['verdicts']}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Bio-Coherence Falsifier: ingest claims into the leaderboard.")
    p.add_argument("--claims", help="JSON file: list of claim dicts")
    p.add_argument("--path", default=None, help="leaderboard JSON path")
    p.add_argument("--self-test", action="store_true", help="seed with built-in claim library")
    p.add_argument("--summary", action="store_true", help="print summary after ingest")
    args = p.parse_args(argv)

    if args.self_test:
        self_test(args.path)
    if args.claims:
        with open(args.claims) as f:
            claims = json.load(f)
        rows = ingest_claims(claims, args.path or "leaderboard.json", source_tag="agent")
        print(f"[ingest] processed {len(rows)} claims")
        for r in rows:
            print(f"  {r['verdict']:>9} | {r['claim']} | ratio={r['ratio_claimed_over_allowed']:.2g}")
    if args.summary or (not args.claims and not args.self_test):
        s = summarize(args.path)
        print(f"TOTAL={s['total']} VERDICTS={s['verdicts']} BASELINE={s['baseline']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
