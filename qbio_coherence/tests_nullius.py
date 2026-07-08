"""Tests for the NULLIUS layer: ledger integrity, attack swarm, cert, board."""

import json
import os
import tempfile
import unittest

from .ledger import Ledger, commit_leaderboard
from .falsify import falsify
from .claims import BUILTIN_CLAIMS, get_claim
from .falsify import report_to_row
from .attack import attack_claim, attack_claims
from .cert import make_certificate
from .board import generate_html, write_board


class TestLedger(unittest.TestCase):
    def _ledger(self):
        d = tempfile.mkdtemp()
        return Ledger(d)

    def test_empty_valid(self):
        v = self._ledger().verify()
        self.assertTrue(v["valid"])
        self.assertEqual(v["count"], 0)

    def test_chain_grows_and_verifies(self):
        l = self._ledger()
        e1 = l.add({"claim": "A", "verdict": "FALSIFIED"})
        e2 = l.add({"claim": "B", "verdict": "SURVIVES"})
        self.assertEqual(e1.seq, 0)
        self.assertEqual(e2.seq, 1)
        self.assertNotEqual(e1.entry_hash, e2.entry_hash)
        self.assertEqual(e1.prev_hash, "")
        self.assertEqual(e2.prev_hash, e1.entry_hash)
        v = l.verify()
        self.assertTrue(v["valid"])
        self.assertEqual(v["count"], 2)

    def test_tamper_detected(self):
        l = self._ledger()
        l.add({"claim": "A", "verdict": "FALSIFIED"})
        l.add({"claim": "B", "verdict": "SURVIVES"})
        # Corrupt a past payload directly in the chain file.
        chain = os.path.join(l.path, "chain.jsonl")
        with open(chain, "r", encoding="utf-8") as f:
            lines = f.readlines()
        obj = json.loads(lines[0])
        obj["payload"]["verdict"] = "SURVIVES"  # tamper
        lines[0] = json.dumps(obj) + "\n"
        with open(chain, "w", encoding="utf-8") as f:
            f.writelines(lines)
        v = l.verify()
        self.assertFalse(v["valid"])
        self.assertEqual(v["broken_at"], 0)

    def test_commit_rows_reset(self):
        l = self._ledger()
        rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
        n = l.commit_rows(rows, reset=True)
        self.assertEqual(n, len(rows))
        self.assertTrue(l.verify()["valid"])

    def test_commit_rows_dedup(self):
        """Re-committing the same rows must NOT duplicate entries (cron guard)."""
        l = self._ledger()
        rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
        n1 = l.commit_rows(rows, reset=True)
        n2 = l.commit_rows(rows)  # second run, same rows
        self.assertEqual(n1, len(rows))
        self.assertEqual(n2, 0, "duplicate commit must append 0")
        self.assertEqual(l.verify()["count"], len(rows))


class TestAttackSwarm(unittest.TestCase):
    def test_all_builtin_attacked(self):
        reps = attack_claims(BUILTIN_CLAIMS)
        self.assertEqual(len(reps), len(BUILTIN_CLAIMS))
        for r in reps:
            self.assertTrue(r.robustness)  # non-empty classification
            self.assertIn(
                r.robustness,
                ("ROBUST", "FRAGILE", "EDGE", "RECOVERABLE", "FIRMLY FALSIFIED",
                 "UNCLASSIFIED"),
            )

    def test_firmenich_null_falsified(self):
        r = attack_claim(get_claim("MT bare electronic (Firmenich null)"))
        # Bare floor with no mechanism -> FALSIFIED (correct), and being exactly
        # at the floor it needs essentially no protection to sit at the boundary.
        self.assertEqual(r.nominal_verdict, "FALSIFIED")
        self.assertLessEqual(r.required_N, 1)

    def test_extreme_claim_firmly_falsified(self):
        # A claim 100 ns above the 13 fs floor (no mechanism declared) is
        # FALSIFIED by the base falsifier (exceeds the floor with nothing to lift
        # it), and the attack swarm shows no physically allowed mechanism could
        # rescue it -> FIRMLY FALSIFIED.
        from .claims import Claim
        extreme = Claim(name="Extreme 100 ns claim", claimed_tau_fs=1e8, kind="electronic")
        r = attack_claim(extreme)
        self.assertEqual(r.nominal_verdict, "FALSIFIED")
        self.assertGreater(r.required_N, 10000)
        self.assertEqual(r.robustness, "FIRMLY FALSIFIED")

    def test_cert_made(self):
        rep = falsify(get_claim("MT bare electronic (Firmenich null)"))
        cert = make_certificate(rep)
        self.assertIn("NULLIUS Verdict Certificate", cert)
        self.assertIn(rep.verdict, cert)


class TestBoard(unittest.TestCase):
    def test_html_generated(self):
        rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
        html = generate_html(rows)
        self.assertIn("<!doctype html>", html)
        for v in ("SURVIVES", "FALSIFIED", "UNTESTED"):
            self.assertIn(v, html)

    def test_html_written(self):
        d = tempfile.mkdtemp()
        out = os.path.join(d, "board.html")
        rows = [report_to_row(falsify(c)) for c in BUILTIN_CLAIMS]
        path = write_board(rows, out)
        self.assertTrue(os.path.exists(path))


class TestCheckCommand(unittest.TestCase):
    def _run(self, *args):
        from .ledger_cli import build_parser
        import io, contextlib
        p = build_parser()
        ns = p.parse_args(["check", *args])
        return ns

    def test_no_mechanism_exceeds_floor_falsified(self):
        ns = self._run("--name", "X", "--tau", "1000",
                        "--protection_mechanism", "none declared")
        from .claims import claim_from_dict
        from .falsify import falsify
        c = claim_from_dict({
            "name": "X", "claimed_tau_fs": 1000.0,
            "protection_mechanism": "none declared",
        })
        self.assertEqual(falsify(c).verdict, "FALSIFIED")

    def test_declared_mechanism_survives(self):
        from .claims import claim_from_dict
        from .falsify import falsify
        c = claim_from_dict({
            "name": "Y", "claimed_tau_fs": 1e9, "kind": "spin",
            "hyperfine": 5.0, "quantum_zeno": 2.0,
            "protection_mechanism": "hyperfine+Zeno",
        })
        self.assertEqual(falsify(c).verdict, "SURVIVES")


if __name__ == "__main__":
    unittest.main(verbosity=2)
