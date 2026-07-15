#!/usr/bin/env python3
"""weekly_publish.py — robust NULLIUS weekly publish step (Firecrawl-free).

Replaces the fragile blind `git push` that broke the Monday cron after the
remote `main` gained GitHub-side commits (LICENSE, templates, etc.), causing
a non-fast-forward rejection and silent pipeline death.

Correct sequence:
  1. git fetch origin
  2. git pull --rebase origin main   (never a blind push)
  3. run discover -> refresh discovered pool (free stack: arXiv + OpenAlex)
  4. rebuild public board (docs/index.html)
  5. commit docs/ changes
  6. git push origin main            (now fast-forwards, safe)
  7. trigger GitHub Pages rebuild via API (so served board updates promptly)

Safety: FALSIFIED verdicts are NEVER auto-committed/published. The ledger_cli
human gate (pending/<slug>.md) is untouched. Only the public SURVIVES/UNTESTED
board and discovered-paper pool are pushed.

Usage:
  python scripts/weekly_publish.py --days 7 --dry-run     # no git ops
  python scripts/weekly_publish.py --days 7              # full publish
"""
import argparse
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.path.expanduser("C:/Users/Admin/AppData/Local/hermes/credentials/.github-token")


def run(cmd, check=True, capture=True):
    print(f"[publish] $ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=REPO, capture_output=capture, text=True)
    if capture:
        out = (r.stdout or "") + (r.stderr or "")
        if out.strip():
            print(out.strip()[:1200])
    if check and r.returncode != 0:
        raise SystemExit(f"[publish] FAILED (exit {r.returncode}): {' '.join(cmd)}")
    return r


def git(args, check=True):
    return run(["git"] + args, check=check)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--dry-run", action="store_true", help="do everything except git push + pages build")
    a = ap.parse_args()

    os.chdir(REPO)

    # 1-2. Sync first (the fix for non-fast-forward deaths).
    git(["fetch", "origin"])
    git(["pull", "--rebase", "origin", "main"])

    # 3. Refresh discovery pool (free stack).
    run([sys.executable, "-m", "qbio_coherence.ledger_cli",
         "discover", "--days", str(a.days), "--out", "_weekly_discovered.json"])

    # 4. Rebuild board.
    run([sys.executable, "-m", "qbio_coherence.ledger_cli",
         "board", "--out", "docs/index.html"])

    # 5. Commit docs only (board output). Never touch pending/ (FALSIFIED gate).
    git(["add", "docs/index.html", "_weekly_discovered.json"])
    # commit only if there is a diff
    st = git(["status", "--porcelain"], check=False)
    if st.stdout.strip():
        git(["commit", "-m", f"weekly board refresh (free-stack discover, {a.days}d)"])
    else:
        print("[publish] no board changes to commit")

    if a.dry_run:
        print("[publish] DRY-RUN complete. No push / no pages build.")
        return

    # 6. Push (safe: already rebased onto origin/main).
    git(["push", "origin", "main"])

    # 7. Trigger GitHub Pages rebuild so the served board updates promptly.
    try:
        tok = open(TOKEN).read().strip()
        import urllib.request, json
        url = "https://api.github.com/repos/CodeGero/qbio-coherence/pages/builds"
        req = urllib.request.Request(
            url, data=b"", headers={
                "Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                "User-Agent": "nullius-publish"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[publish] Pages rebuild triggered: HTTP {resp.status}")
    except Exception as e:
        print(f"[publish] WARN: Pages rebuild trigger failed ({e}); CDN will catch up on next push.")


if __name__ == "__main__":
    main()
