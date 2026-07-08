"""Command-line interface for the Bio-Coherence Falsifier."""

import argparse
import json
import sys

from .baseline import (
    FIRMENICH_T_COH,
    FIRMENICH_GAMMA_DEPHASE,
    T_BODY,
    bare_coherence_time,
)
from .claims import BUILTIN_CLAIMS, get_claim
from .falsify import falsify, falsify_all
from .leaderboard import load_board, summarize


def _fmt_fs(fs: float) -> str:
    if fs >= 1e9:
        return f"{fs/1e9:.3g} us"
    if fs >= 1e6:
        return f"{fs/1e6:.3g} ps"
    if fs >= 1e3:
        return f"{fs/1e3:.3g} ns"
    return f"{fs:.3g} fs"


def cmd_list(args):
    for c in BUILTIN_CLAIMS:
        print(f"  - {c.name}  [{c.kind}]  claimed={_fmt_fs(c.claimed_tau_fs)}")
    return 0


def cmd_check(args):
    if args.name:
        claim = get_claim(args.name)
        reports = [falsify(claim)]
    else:
        reports = falsify_all()

    for r in reports:
        print("=" * 70)
        print(f"CLAIM : {r.claim_name}")
        print(f"KIND  : {r.kind}   T={r.temperature_K} K")
        print(f"BARE  : {_fmt_fs(r.bare_tau_fs)}  (dephasing floor)")
        print(f"PROT  : x{r.protection_factor:.3g}  [{r.mechanism}]")
        print(f"ALLOWED: {_fmt_fs(r.allowed_tau_fs)}")
        print(f"CLAIMED: {_fmt_fs(r.claimed_tau_fs)}")
        print(f"RATIO : claimed/allowed = {r.ratio:.3g}")
        print(f"VERDICT: {r.verdict}")
        print(f"WHY   : {r.failure_mode}")
        print(f"BASE  : {r.baseline_source}")
        print(f"SRC   : {r.claim_source}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump([r.as_dict() for r in reports], f, indent=2)
        print(f"\n[wrote JSON to {args.json}]")
    return 0


def cmd_board(args):
    if args.summary:
        s = summarize(args.path)
        print(f"Total claims : {s['total']}")
        print(f"Verdicts     : {s['verdicts']}")
        print(f"Baseline     : {s['baseline']}")
        return 0
    board = load_board(args.path)
    for e in board["entries"]:
        print("=" * 70)
        print(f"{e['verdict']:>9} | {e['claim']}")
        print(f"  claimed={_fmt_fs(e['claimed_tau_fs'])}  allowed={_fmt_fs(e['allowed_tau_fs'])}  "
              f"ratio={e['ratio_claimed_over_allowed']:.2g}  prot=x{e['protection_factor']:.2g}")
        print(f"  mech={e['mechanism']}")
        print(f"  src ={e['claim_source']}")
    return 0


def cmd_baseline(args):
    print(f"Firmenich et al. (2026) HEOM baseline @ {T_BODY} K:")
    print(f"  gamma_dephase = {FIRMENICH_GAMMA_DEPHASE:.3e} Hz")
    print(f"  tau_coh       = {FIRMENICH_T_COH*1e15:.3g} fs")
    print(f"  tau_coh(T)    = {bare_coherence_time(args.t)*1e15:.3g} fs @ {args.t} K")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="qbio-falsify",
        description="Bio-Coherence Falsifier: falsify biological quantum-coherence claims against the Firmenich 2026 HEOM baseline.",
    )
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("list", help="list built-in falsifiable claims")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("check", help="falsify a claim (or all)")
    sp.add_argument("name", nargs="?", help="claim name (default: all)")
    sp.add_argument("--json", help="write report as JSON to this path")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("board", help="show the coherence leaderboard")
    sp.add_argument("--path", default=None, help="leaderboard JSON path")
    sp.add_argument("--summary", action="store_true", help="print summary only")
    sp.set_defaults(func=cmd_board)

    sp = sub.add_parser("baseline", help="print the dephasing baseline")
    sp.add_argument("--t", type=float, default=T_BODY, help="temperature (K)")
    sp.set_defaults(func=cmd_baseline)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
