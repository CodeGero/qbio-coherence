"""Core falsification engine.

Compares a claimed coherence time against the effective coherence time allowed
by the Firmenich baseline plus any declared protection mechanisms, and emits a
verdict with a failure mode (falsification condition).
"""

from dataclasses import dataclass, field
from typing import Optional

from .baseline import (
    FIRMENICH_T_COH,
    T_BODY,
    bare_coherence_time,
)
from .protection import (
    effective_coherence_time,
    total_protection_factor,
)
from .claims import Claim

# Margin: a claim must SURVIVE the baseline by at least this ratio to be
# considered "survives" rather than "borderline/falsified". Honest threshold:
# if claimed <= 2x the allowed effective time, treat as not establishing
# functional coherence (decoherence dominates within experimental error).
SURVIVE_MARGIN = 2.0


@dataclass
class Report:
    claim_name: str
    kind: str
    temperature_K: float
    bare_tau_fs: float
    protection_factor: float
    allowed_tau_fs: float
    claimed_tau_fs: float
    ratio: float  # claimed / allowed
    verdict: str  # SURVIVES | FALSIFIED | UNTESTED
    mechanism: str
    failure_mode: str
    baseline_source: str
    claim_source: str
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "claim": self.claim_name,
            "kind": self.kind,
            "temperature_K": self.temperature_K,
            "bare_tau_fs": self.bare_tau_fs,
            "protection_factor": self.protection_factor,
            "allowed_tau_fs": self.allowed_tau_fs,
            "claimed_tau_fs": self.claimed_tau_fs,
            "ratio_claimed_over_allowed": self.ratio,
            "verdict": self.verdict,
            "mechanism": self.mechanism,
            "failure_mode": self.failure_mode,
            "baseline_source": self.baseline_source,
            "claim_source": self.claim_source,
            "notes": self.notes,
        }


def falsify(claim: Claim) -> Report:
    """Run the falsifier on a single Claim and return a Report."""
    kind = claim.kind
    if kind == "electronic":
        bare_tau = bare_coherence_time(claim.temperature_K)
        baseline_source = (
            "Firmenich et al. 2026, HEOM, gamma=7.69e13 Hz, tau~13 fs @310K"
        )
    elif kind == "spin":
        # Spin regime: use the spin baseline (not Firmenich electronic floor).
        from .baseline import SPIN_T_COH

        bare_tau = SPIN_T_COH
        baseline_source = (
            "Ritz et al. 2000 / Hore & Mouritsen 2016 (radical-pair spin coherence, tau~1 us)"
        )
    else:
        raise ValueError(f"unknown kind: {kind!r}")

    prot = total_protection_factor(
        claim.n_collective, claim.non_markovian, claim.entropy,
        claim.structured_bath, claim.quantum_zeno, claim.hyperfine, claim.kind,
    )
    allowed_tau = bare_tau * prot  # seconds
    claimed_tau = claim.claimed_tau_seconds()  # seconds

    bare_tau_fs = bare_tau * 1e15
    allowed_tau_fs = allowed_tau * 1e15
    claimed_tau_fs = claimed_tau * 1e15
    ratio = claimed_tau / allowed_tau if allowed_tau > 0 else float("inf")

    # Verdict logic.
    # SURVIVES: claimed coherence is (within margin) permitted by the baseline +
    #   declared protection. Physics-consistent. Still needs experimental proof.
    # FALSIFIED: claimed coherence exceeds what the declared mechanism can permit
    #   by more than the margin -> the mechanism as specified cannot support it.
    # UNTESTED: no protection mechanism declared, but claim is within experimental
    #   reach -> not ruled out by physics alone; requires a declared mechanism + data.
    declared_mechanism = not (
        claim.protection_mechanism == "none (bare baseline)"
        or claim.protection_mechanism == "none declared"
        or (prot == 1.0 and claim.kind == "electronic")
    )

    if claimed_tau <= allowed_tau * SURVIVE_MARGIN:
        # Claim is within (or below) what the declared physics permits.
        if declared_mechanism:
            verdict = "SURVIVES"
            failure_mode = (
                f"Claimed tau ({claimed_tau_fs:.1f} fs) is within the protected "
                f"allowed window (~{allowed_tau_fs:.1f} fs with "
                f"{claim.protection_mechanism}). Physics-consistent. Still requires "
                "experimental confirmation and an independent replication."
            )
        else:
            # No mechanism: the dephasing floor itself is the only reference.
            verdict = "FALSIFIED"
            failure_mode = (
                "No protection mechanism declared. Claimed coherence exceeds the "
                f"bare dephasing floor ({bare_tau_fs:.1f} fs @310K) with nothing to "
                "lift it. Falsified unless a specific, quantified protection "
                "mechanism is supplied."
            )
    else:
        # Claim exceeds what the declared mechanism can permit.
        if declared_mechanism:
            verdict = "FALSIFIED"
            failure_mode = (
                f"Declared protection ({claim.protection_mechanism}) permits at most "
                f"~{allowed_tau_fs:.1f} fs, but claim is {claimed_tau_fs:.1f} fs "
                f"({ratio:.1f}x over). Mechanism as specified is insufficient; "
                "falsified unless a stronger, justified protection is demonstrated."
            )
        else:
            verdict = "FALSIFIED"
            failure_mode = (
                "Claim exceeds the bare dephasing floor and no protection mechanism "
                f"is declared. The floor alone ({bare_tau_fs:.1f} fs @310K) cannot "
                f"permit {claimed_tau_fs:.1f} fs with nothing to lift it. Falsified "
                "unless a specific, quantified protection mechanism is supplied."
            )

    return Report(
        claim_name=claim.name,
        kind=kind,
        temperature_K=claim.temperature_K,
        bare_tau_fs=bare_tau_fs,
        protection_factor=prot,
        allowed_tau_fs=allowed_tau_fs,
        claimed_tau_fs=claimed_tau_fs,
        ratio=ratio,
        verdict=verdict,
        mechanism=claim.protection_mechanism,
        failure_mode=failure_mode,
        baseline_source=baseline_source,
        claim_source=claim.claim_source,
        notes=claim.notes,
    )


def report_to_row(r: Report) -> dict:
    """Flat row for leaderboard/JSON accumulation (claim + verdict together)."""
    return {
        "claim": r.claim_name,
        "kind": r.kind,
        "temperature_K": r.temperature_K,
        "claimed_tau_fs": r.claimed_tau_fs,
        "bare_tau_fs": r.bare_tau_fs,
        "protection_factor": r.protection_factor,
        "allowed_tau_fs": r.allowed_tau_fs,
        "ratio_claimed_over_allowed": r.ratio,
        "verdict": r.verdict,
        "mechanism": r.mechanism,
        "failure_mode": r.failure_mode,
        "baseline_source": r.baseline_source,
        "claim_source": r.claim_source,
        "notes": r.notes,
    }


def falsify_all(claims=None) -> list[Report]:
    from .claims import BUILTIN_CLAIMS

    claims = claims if claims is not None else BUILTIN_CLAIMS
    return [falsify(c) for c in claims]
