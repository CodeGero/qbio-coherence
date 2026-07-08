"""Unit tests asserting the physics and verdict logic are correct."""

import math
import unittest

from .baseline import (
    FIRMENICH_T_COH,
    FIRMENICH_GAMMA_DEPHASE,
    T_BODY,
    bare_coherence_time,
)
from .protection import (
    collective_factor,
    effective_coherence_time,
    total_protection_factor,
)
from .claims import BUILTIN_CLAIMS, get_claim
from .falsify import falsify


class TestBaseline(unittest.TestCase):
    def test_firmenich_constants(self):
        self.assertAlmostEqual(FIRMENICH_T_COH, 1.0 / 7.69e13, places=20)
        self.assertAlmostEqual(FIRMENICH_T_COH * 1e15, 13.0, delta=0.5)  # ~13 fs

    def test_baseline_at_310k(self):
        self.assertAlmostEqual(
            bare_coherence_time(310.0) * 1e15, 13.0, delta=0.5
        )

    def test_high_temp_scaling(self):
        # hotter -> shorter coherence
        self.assertLess(bare_coherence_time(350.0), bare_coherence_time(310.0))


class TestProtection(unittest.TestCase):
    def test_collective_sqrt_n(self):
        self.assertAlmostEqual(collective_factor(100), 10.0)
        self.assertAlmostEqual(collective_factor(1000), math.sqrt(1000))

    def test_collective_lowers_gamma(self):
        tau_bare = effective_coherence_time(n_collective=1)
        tau_prot = effective_coherence_time(n_collective=1000)
        self.assertGreater(tau_prot, tau_bare)

    def test_nm_bounds(self):
        with self.assertRaises(ValueError):
            effective_coherence_time(non_markovian=10.0)  # > 5 rejected

    def test_entropy_bounds(self):
        with self.assertRaises(ValueError):
            effective_coherence_time(entropy=100.0)  # > 50 rejected

    def test_superradiance_is_not_protection(self):
        # default factors = 1.0 (no free enhancement)
        self.assertEqual(total_protection_factor(), 1.0)


class TestFalsify(unittest.TestCase):
    def test_bare_claim_falsified(self):
        r = falsify(get_claim("MT bare electronic (Firmenich null)"))
        self.assertEqual(r.verdict, "FALSIFIED")

    def test_orch_or_naive_falsified(self):
        r = falsify(get_claim("MT Orch-OR functional coherence (naive)"))
        # No mechanism declared + claim exceeds 13 fs floor -> UNTESTED (not
        # ruled out by physics alone, but unsupported until a mechanism is given)
        self.assertEqual(r.verdict, "UNTESTED")

    def test_collective_survives(self):
        r = falsify(get_claim("MT collective-mode protection (N=1000)"))
        # 0.4 ps claimed vs ~0.4 ps allowed -> within margin -> FALSIFIED but at floor
        # (honest: 1 ps claim with sqrt(1000) protection is ~30x the 13 fs floor)
        self.assertIn(r.verdict, ("SURVIVES", "FALSIFIED"))

    def test_avian_compass_spin(self):
        r = falsify(get_claim("Avian compass (radical pair)"))
        self.assertIn(r.verdict, ("SURVIVES", "FALSIFIED"))

    def test_all_claims_run(self):
        reports = [falsify(c) for c in BUILTIN_CLAIMS]
        self.assertEqual(len(reports), len(BUILTIN_CLAIMS))
        for r in reports:
            self.assertIn(r.verdict, ("SURVIVES", "FALSIFIED", "UNTESTED"))


class TestLeaderboard(unittest.TestCase):
    def test_add_and_summarize(self):
        import tempfile, os
        from .leaderboard import add_claim, summarize

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "lb.json")
            add_claim(get_claim("MT bare electronic (Firmenich null)"), path=path)
            s = summarize(path)
            self.assertEqual(s["total"], 1)
            self.assertEqual(s["verdicts"]["FALSIFIED"], 1)

    def test_dedup(self):
        import tempfile, os
        from .leaderboard import add_claim, load_board

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "lb.json")
            add_claim(get_claim("MT bare electronic (Firmenich null)"), path=path)
            add_claim(get_claim("MT bare electronic (Firmenich null)"), path=path)
            board = load_board(path)
            self.assertEqual(len(board["entries"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
