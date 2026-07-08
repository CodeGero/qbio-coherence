"""Bio-Coherence Falsifier.

A computational falsification engine for biological quantum-coherence claims.
Every verdict is anchored to the Firmenich et al. (2026) HEOM dephasing
baseline (gamma_dephase = 7.69e13 Hz, tau_coh ~ 13 fs at 310 K), which is the
rigorous reference for electronic coherence in protein environments and MUST be
cited by any claim of functional biological quantum coherence.
"""

from .baseline import (
    FIRMENICH_GAMMA_DEPHASE,
    FIRMENICH_T_COH,
    T_BODY,
    bare_coherence_time,
)
from .protection import (
    collective_factor,
    non_markovian_factor,
    entropy_feedback_factor,
    effective_dephase_rate,
    effective_coherence_time,
)
from .falsify import falsify, Claim, Report
from .claims import BUILTIN_CLAIMS, get_claim
from .falsify import falsify, falsify_all
from .leaderboard import load_board, add_claim, add_from_dict, summarize
from .ingest import ingest_claims, self_test
from .ledger import Ledger, commit_leaderboard
from .attack import attack_claims, attack_claim
from .cert import make_certificate
from .board import generate_html, write_board
__version__ = "0.3.2"
__all__ = [
    "FIRMENICH_GAMMA_DEPHASE",
    "FIRMENICH_T_COH",
    "T_BODY",
    "bare_coherence_time",
    "collective_factor",
    "non_markovian_factor",
    "entropy_feedback_factor",
    "effective_dephase_rate",
    "effective_coherence_time",
    "falsify",
    "Claim",
    "Report",
    "BUILTIN_CLAIMS",
    "load_board",
    "add_claim",
    "add_from_dict",
    "summarize",
    "ingest_claims",
    "self_test",
    "Ledger",
    "commit_leaderboard",
    "attack_claims",
    "attack_claim",
    "make_certificate",
    "generate_html",
    "write_board",
]
