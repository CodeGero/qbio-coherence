"""NULLIUS CLI: ledger, attack swarm, certificate, and public board.

Subcommands:
  nullius commit     Seed the ledger from the leaderboard (deterministic verdicts).
  nullius verify     Recompute the full hash chain and report tamper status.
  nullius attack     Run the adversarial sensitivity swarm over built-in claims.
  nullius cert       Emit a verdict certificate (markdown) for a named claim.
  nullius board      Generate the static public HTML truth board.

Run as: python -m qbio_coherence.ledger_cli <cmd> [args]
"""

import argparse
import json
import os
import re
import sys

from .claims import BUILTIN_CLAIMS, get_claim
from .falsify import falsify
from .ledger import Ledger, commit_leaderboard, DEFAULT_LEDGER_DIR
from .leaderboard import load_board, DEFAULT_PATH as LB_PATH
from .attack import attack_claims, attack_claim
from .cert import make_certificate
from .board import write_board
from .discover import discover
from .falsify import report_to_row


def cmd_commit(args):
    ledger = Ledger(args.ledger)
    if args.leaderboard:
        n = commit_leaderboard(args.leaderboard, args.ledger, reset=args.reset)
        print(f"[nullius] committed {n} leaderboard rows to ledger.")
    else:
        # Commit the built-in claim library directly (no leaderboard needed).
        rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
        n = ledger.commit_rows(rows, reset=args.reset)
        print(f"[nullius] committed {n} built-in verdict rows to ledger.")
    v = ledger.verify()
    print(f"[nullius] ledger verify -> valid={v['valid']} count={v['count']}")
    return 0


def cmd_verify(args):
    v = Ledger(args.ledger).verify()
    if v["valid"]:
        print(f"LEDGER VALID. entries={v['count']}")
        return 0
    print(f"LEDGER TAMPERED at entry #{v['broken_at']}: {v['reason']}")
    return 1


def cmd_attack(args):
    reports = attack_claims(BUILTIN_CLAIMS)
    print("=" * 72)
    print("NULLIUS ADVERSARIAL SENSITIVITY SWARM")
    print("=" * 72)
    for r in reports:
        print(f"\nCLAIM  : {r.claim} [{r.kind}]")
        print(f"VERDICT: {r.nominal_verdict}  ->  ROBUSTNESS: {r.robustness}")
        print(f"  bare ratio (claimed/floor) : {r.bare_ratio:.3g}")
        print(f"  declared protection factor : x{r.declared_pf:.3g}")
        print(f"  min pf to survive          : x{r.min_pf_to_survive:.3g}")
        print(f"  protection slack            : {r.protection_slack:.3g}x")
        print(f"  claimed slack (to flip)     : {r.claimed_slack:.3g}x")
        if r.required_N > 1:
            print(f"  required N_collective       : {r.required_N:,}")
        if r.flip_mechanism:
            print(f"  flip if                    : {r.flip_mechanism}")
        print(f"  note                       : {r.notes}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([r.as_dict() for r in reports], f, indent=2)
        print(f"\n[wrote attack report to {args.json}]")
    return 0


def cmd_cert(args):
    claim = get_claim(args.name)
    report = falsify(claim)
    ledger = Ledger(args.ledger)
    # Commit on the fly and attach the entry hash so the cert is verifiable.
    entry = ledger.add(report_to_row(report))
    cert = make_certificate(report, entry, ledger_dir=args.ledger)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(cert)
        print(f"[nullius] certificate written to {args.out} (ledger #{entry.seq})")
    else:
        print(cert)
    return 0


def cmd_check(args):
    """One-shot falsification of a user-supplied claim (third-party usability).

    Accepts a JSON file (--json, list of claim dicts) or inline fields, runs the
    falsifier, prints the verdict + failure mode for each, and (with --commit)
    appends surviving/UNTESTED verdicts to the ledger. FALSIFIED verdicts are
    written to pending/ as drafts and NEVER auto-committed (human gate).
    """
    from .claims import claim_from_dict, Claim
    from .falsify import falsify as _falsify, report_to_row

    if args.json:
        with open(args.json) as f:
            raw = json.load(f)
        claims = [claim_from_dict(c) if isinstance(c, dict) else c for c in raw]
    else:
        if not args.name:
            print("ERROR: provide --json <file> or --name <claim> --tau <fs>")
            return 2
        claims = [Claim(
            name=args.name,
            claimed_tau_fs=float(args.tau),
            kind=args.kind,
            temperature_K=float(args.temperature_K),
            n_collective=int(args.n_collective),
            non_markovian=float(args.non_markovian),
            entropy=float(args.entropy),
            structured_bath=float(args.structured_bath),
            quantum_zeno=float(args.quantum_zeno),
            hyperfine=float(args.hyperfine),
            protection_mechanism=args.protection_mechanism,
            claim_source=args.claim_source or "user-supplied (nullius check)",
            notes=args.notes or "",
        )]

    ledger = Ledger(args.ledger) if args.commit else None
    pending_dir = _pending_dir()
    for c in claims:
        rep = _falsify(c)
        row = report_to_row(rep)
        print("=" * 72)
        print(f"CLAIM  : {rep.claim_name} [{rep.kind}]")
        print(f"VERDICT: {rep.verdict}")
        print(f"  claimed tau : {rep.claimed_tau_fs:.1f} fs")
        print(f"  allowed tau : {rep.allowed_tau_fs:.1f} fs (prot x{rep.protection_factor:.3g})")
        print(f"  ratio       : {rep.ratio:.2g}x")
        print(f"  mechanism   : {rep.mechanism}")
        print(f"  FAILURE MODE: {rep.failure_mode}")
        if rep.verdict == "FALSIFIED":
            slug = re.sub(r"[^a-z0-9]+", "-", rep.claim_name.lower()).strip("-")
            pdraft = os.path.join(pending_dir, f"{slug}.md")
            with open(pdraft, "w", encoding="utf-8") as pf:
                pf.write(_draft_md(rep, row))
            print(f"  -> FALSIFIED draft written to pending/{slug}.md (human review required)")
        elif args.commit and ledger is not None:
            ledger.add(row)
            print(f"  -> committed to ledger (#{ledger._count()-1})")
    if args.commit and ledger is not None:
        v = ledger.verify()
        print(f"\n[nullius] ledger verify -> valid={v['valid']} count={v['count']}")
    return 0


def _pending_dir():
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pending")
    os.makedirs(d, exist_ok=True)
    return d


def _draft_md(rep, row):
    return f"""# FALSIFIED DRAFT — pending human review

**Claim:** {rep.claim_name}
**Kind:** {rep.kind}
**Claimed tau:** {rep.claimed_tau_fs:.1f} fs
**Allowed tau (Firmenich floor + declared mechanism):** {rep.allowed_tau_fs:.1f} fs
**Ratio claimed/allowed:** {rep.ratio:.2g}x
**Declared mechanism:** {rep.mechanism}
**Failure mode:** {rep.failure_mode}
**Baseline:** {rep.baseline_source}
**Source:** {rep.claim_source}

> This draft was generated by the NULLIUS cron. Do NOT publish until a human
> reviews the extracted claim and confirms the coherence time was stated (not
> inferred) and the mechanism is fairly characterized.
"""


def cmd_board(args):
    rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
    out = args.out or "nullius_board.html"
    path = write_board(rows, out)
    print(f"[nullius] public board written to {path}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="qbio-falsify nullius",
        description="NULLIUS: tamper-evident verdict ledger, adversarial attack swarm, and public truth board.",
    )
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("commit", help="seed the ledger from verdicts")
    sp.add_argument("--ledger", default=DEFAULT_LEDGER_DIR)
    sp.add_argument("--leaderboard", default=None)
    sp.add_argument("--reset", action="store_true", help="clear ledger first (dev only)")
    sp.set_defaults(func=cmd_commit)

    sp = sub.add_parser("verify", help="verify ledger integrity")
    sp.add_argument("--ledger", default=DEFAULT_LEDGER_DIR)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("attack", help="run adversarial sensitivity swarm")
    sp.add_argument("--json", default=None, help="write attack report JSON")
    sp.set_defaults(func=cmd_attack)

    sp = sub.add_parser("cert", help="emit a verdict certificate")
    sp.add_argument("name", help="claim name")
    sp.add_argument("--ledger", default=DEFAULT_LEDGER_DIR)
    sp.add_argument("--out", default=None, help="write markdown to path")
    sp.set_defaults(func=cmd_cert)

    sp = sub.add_parser("discover", help="scan arXiv+OpenAlex for recent coherence papers")
    sp.add_argument("--days", type=int, default=10)
    sp.add_argument("--out", default="new_papers.json")
    sp.add_argument("--max-per", type=int, default=12)
    sp.set_defaults(func=cmd_discover)

    sp = sub.add_parser("board", help="generate static public HTML board")
    sp.add_argument("--out", default=None)
    sp.set_defaults(func=cmd_board)

    sp = sub.add_parser("check", help="falsify a user-supplied claim (one-shot)")
    sp.add_argument("--json", default=None, help="JSON file: list of claim dicts")
    sp.add_argument("--name", default=None, help="claim name (inline mode)")
    sp.add_argument("--tau", type=float, default=None, help="claimed coherence time in fs")
    sp.add_argument("--kind", default="electronic", help="electronic | spin")
    sp.add_argument("--temperature_K", type=float, default=310.0)
    sp.add_argument("--n_collective", type=int, default=1)
    sp.add_argument("--non_markovian", type=float, default=1.0)
    sp.add_argument("--entropy", type=float, default=1.0)
    sp.add_argument("--structured_bath", type=float, default=1.0)
    sp.add_argument("--quantum_zeno", type=float, default=1.0)
    sp.add_argument("--hyperfine", type=float, default=1.0)
    sp.add_argument("--protection_mechanism", default="none declared")
    sp.add_argument("--claim_source", default=None)
    sp.add_argument("--notes", default=None)
    sp.add_argument("--commit", action="store_true", help="append SURVIVES/UNTESTED to ledger")
    sp.add_argument("--ledger", default=DEFAULT_LEDGER_DIR)
    sp.set_defaults(func=cmd_check)

    return p


def cmd_discover(args):
    from .discover import discover as _discover
    uniq = _discover(args.days, args.max_per)
    with open(args.out, "w", encoding="utf-8") as f:
        import json
        json.dump(uniq, f, indent=2)
    print(f"[nullius] discover -> {len(uniq)} unique papers in last {args.days} d -> {args.out}")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
