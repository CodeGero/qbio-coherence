"""Built-in coherence claims (the standard library of things to falsify).

Each claim is a falsifiable statement: a claimed coherence time at a temperature
for an electronic or spin system. The falsifier compares it against the
appropriate baseline + any declared protection, and emits a verdict.

Source tags let the agent layer attribute each verdict and let users audit the
provenance. 'claim_source' is the citation for the CLAIM; the baseline source is
always Firmenich et al. (2026) (or Ritz/Hore for spin).
"""

from dataclasses import dataclass, field
from typing import Optional

from .baseline import T_BODY, FIRMENICH_T_COH, SPIN_T_COH


@dataclass
class Claim:
    """A single falsifiable biological quantum-coherence claim."""

    name: str
    claimed_tau_fs: float  # claimed coherence time, in FEMTOSECONDS
    kind: str = "electronic"  # "electronic" or "spin"
    temperature_K: float = T_BODY
    n_collective: int = 1
    non_markovian: float = 1.0
    entropy: float = 1.0
    structured_bath: float = 1.0
    quantum_zeno: float = 1.0
    hyperfine: float = 1.0
    protection_mechanism: str = "none (bare baseline)"
    claim_source: str = "unspecified"
    notes: str = ""

    def claimed_tau_seconds(self) -> float:
        return self.claimed_tau_fs * 1e-15

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "claimed_tau_fs": self.claimed_tau_fs,
            "kind": self.kind,
            "temperature_K": self.temperature_K,
            "n_collective": self.n_collective,
            "non_markovian": self.non_markovian,
            "entropy": self.entropy,
            "structured_bath": self.structured_bath,
            "quantum_zeno": self.quantum_zeno,
            "hyperfine": self.hyperfine,
            "protection_mechanism": self.protection_mechanism,
            "claim_source": self.claim_source,
            "notes": self.notes,
        }


def claim_from_dict(d: dict) -> "Claim":
    return Claim(
        name=d["name"],
        claimed_tau_fs=float(d["claimed_tau_fs"]),
        kind=d.get("kind", "electronic"),
        temperature_K=float(d.get("temperature_K", T_BODY)),
        n_collective=int(d.get("n_collective", 1)),
        non_markovian=float(d.get("non_markovian", 1.0)),
        entropy=float(d.get("entropy", 1.0)),
        structured_bath=float(d.get("structured_bath", 1.0)),
        quantum_zeno=float(d.get("quantum_zeno", 1.0)),
        hyperfine=float(d.get("hyperfine", 1.0)),
        protection_mechanism=d.get("protection_mechanism", "none declared"),
        claim_source=d.get("claim_source", "unspecified"),
        notes=d.get("notes", ""),
    )


# --- Built-in claims spanning the field --------------------------------------
BUILTIN_CLAIMS = [
    Claim(
        name="MT bare electronic (Firmenich null)",
        claimed_tau_fs=FIRMENICH_T_COH * 1e15,  # ~13 fs
        kind="electronic",
        protection_mechanism="none (dephasing floor)",
        claim_source="Firmenich et al. 2026, HEOM, 1JFF Trp network @310K",
        notes="The honest null hypothesis. Any protection claim is measured against this.",
    ),
    Claim(
        name="MT Orch-OR functional coherence (naive)",
        claimed_tau_fs=1e6,  # ~1 ps is the soft floor often invoked
        kind="electronic",
        protection_mechanism="none declared",
        claim_source="Hameroff-Penrose Orch-OR (various); unspecified mechanism",
        notes="Often asserted without a protection mechanism. Should be FALSIFIED unless one is declared.",
    ),
    Claim(
        name="MT collective-mode protection (N=1000)",
        claimed_tau_fs=400.0,  # 0.4 ps, matches audit's sqrt(1000) estimate
        kind="electronic",
        n_collective=1000,
        protection_mechanism="collective-mode / Quantum Darwinism (1/sqrt N)",
        claim_source="Gross & Haroche 1982; Zurek 2009; audit ATP_QEC_DEPHASING_AUDIT.md",
        notes="Plausible if N_coherent ~ 1000 Trp are truly phase-locked. Falsifiable via 2P-FLIM.",
    ),
    Claim(
        name="Avian compass (radical pair)",
        claimed_tau_fs=1e9,  # ~1 us spin coherence
        kind="spin",
        hyperfine=5.0,
        quantum_zeno=2.0,
        protection_mechanism="hyperfine protection (quantum needle) + quantum Zeno",
        claim_source="Ritz et al. 2000; Hore & Mouritsen 2016; Kritman et al. 2025 (Zeno)",
        notes="Spin regime; distinct baseline (tau ~ 1 us). Established, not the Firmenich floor.",
    ),
    Claim(
        name="Photosynthetic EET (FMO)",
        claimed_tau_fs=600.0,  # ~0.6 ps observed electronic coherence
        kind="electronic",
        n_collective=7,
        structured_bath=18.0,
        protection_mechanism="environment-assisted transport / structured bath (ENAQT)",
        claim_source="Engel et al. 2007; Panitchayangkoon et al. 2010",
        notes="Short-lived but experimentally observed. Structured spectral density is the documented mechanism.",
    ),
    Claim(
        name="Collagen-piezo proton tunneling (Stark-shifted)",
        claimed_tau_fs=50.0,  # speculative ps-scale proton process
        kind="electronic",
        n_collective=10,
        protection_mechanism="collagen piezoelectric field Stark modulation",
        claim_source="Mana dissertation (Kryptorious QB KB); speculative",
        notes="PHYSICAL POSSIBILITY, not demonstrated biological function. Flagged accordingly.",
    ),
]


def get_claim(name: str) -> Claim:
    for c in BUILTIN_CLAIMS:
        if c.name.lower() == name.lower():
            return c
    raise KeyError(f"unknown claim: {name!r}")
