"""NULLIUS attack swarm: adversarial sensitivity probing of verdicts.

The falsifier emits a single verdict for a claim as *specified*. The attack
swarm asks the harder question: how robust is that verdict to the *range* of
physically allowed parameters? A claim that "SURVIVES" only because its declared
protection factor sits at the single most favorable value is fragile and should
be flagged before it enters the scientific record.

This is the automated adversarial peer review: it probes every verdict across
the literature-supported parameter bounds and reports whether the verdict holds
at the extremes or collapses, plus the critical parameter value at which it
flips.

Robustness classes:
  ROBUST            verdict holds across the full allowed parameter range.
  FRAGILE           verdict holds but a small (<=2x) parameter change flips it.
  EDGE              verdict holds but only at the extreme of what is declared.
  RECOVERABLE       nominally FALSIFIED/UNTESTED but a plausible mechanism could
                    rescue it (required N_collective is physically achievable).
  FIRMLY FALSIFIED  even the maximum physically allowed mechanism cannot rescue
                    the claim -> it is dead under this baseline.
"""

from dataclasses import dataclass

from .claims import Claim, BUILTIN_CLAIMS, claim_from_dict
from .falsify import falsify

# Literature-supported maxima used to bound "what mechanism could rescue a claim".
# (See protection.py honesty constraints.) These define the realistic envelope.
NM_MAX = 5.0
ENTROPY_MAX = 50.0
STRUCTURED_MAX = 20.0
ZENO_MAX = 50.0
HYPERFINE_MAX = 10.0
# Physically plausible ceiling on coherently phase-locked chromophores.
# A microtubule has ~13 protofilaments; realistic coherent N is at most ~1e4.
N_PLAUSIBLE = 1000
N_STRETCH = 10000


@dataclass
class AttackReport:
    claim: str
    kind: str
    nominal_verdict: str
    bare_ratio: float          # claimed / bare (no-protection ratio)
    declared_pf: float         # total declared protection factor
    min_pf_to_survive: float   # bare_ratio / 2  (SURVIVES needs claimed <= 2*allowed)
    protection_slack: float    # declared_pf / min_pf_to_survive
    claimed_slack: float       # 2 / (claimed/allowed); >1 means room before flip
    required_N: int            # N_collective needed to rescue (electronic)
    robustness: str
    flip_mechanism: str
    notes: str

    def as_dict(self) -> dict:
        return {
            "claim": self.claim,
            "kind": self.kind,
            "nominal_verdict": self.nominal_verdict,
            "bare_ratio": self.bare_ratio,
            "declared_pf": self.declared_pf,
            "min_pf_to_survive": self.min_pf_to_survive,
            "protection_slack": self.protection_slack,
            "claimed_slack": self.claimed_slack,
            "required_N": self.required_N,
            "robustness": self.robustness,
            "flip_mechanism": self.flip_mechanism,
            "notes": self.notes,
        }


def _other_max(kind: str) -> float:
    """Maximum non-collective protection product allowed by the bounds."""
    if kind == "spin":
        return NM_MAX * ZENO_MAX * HYPERFINE_MAX
    return NM_MAX * ENTROPY_MAX * STRUCTURED_MAX


def attack_claim(claim: Claim) -> AttackReport:
    r = falsify(claim)
    bare = r.bare_tau_fs
    claimed = r.claimed_tau_fs
    bare_ratio = claimed / bare if bare > 0 else float("inf")
    declared_pf = r.protection_factor
    min_pf = bare_ratio / 2.0  # SURVIVES needs claimed <= 2 * bare * pf
    protection_slack = declared_pf / min_pf if min_pf > 0 else float("inf")
    ratio_allowed = bare_ratio / declared_pf if declared_pf > 0 else float("inf")
    claimed_slack = 2.0 / ratio_allowed if ratio_allowed > 0 else float("inf")

    # Required collective N to rescue, assuming we max out all other factors.
    other_max = _other_max(claim.kind)
    required_collective_pf = min_pf / other_max if other_max > 0 else float("inf")
    required_N = max(1, int(required_collective_pf ** 2 + 0.999))

    verdict = r.verdict
    robustness = ""
    flip = ""
    notes = ""

    if verdict == "SURVIVES":
        if protection_slack >= 2.0 and claimed_slack >= 1.5:
            robustness = "ROBUST"
            notes = ("Verdict holds across the allowed range; mechanism has real "
                     "slack and the claimed coherence is well under the 2x flip line.")
        elif protection_slack >= 1.1 and claimed_slack >= 1.1:
            robustness = "FRAGILE"
            flip = (f"reduce N_collective below ~{int((declared_pf / (claimed_slack)) ** 2)} "
                    f"or raise claimed tau > 2x allowed")
            notes = ("Verdict holds but with limited slack; a modest error in the "
                     "declared mechanism or a small measurement overrun would flip it.")
        else:
            robustness = "EDGE"
            flip = "any reduction in declared protection or small claimed-tau increase"
            notes = ("Verdict survives only at the extreme of what is declared; "
                     "effectively on the boundary of falsification.")
    elif verdict in ("FALSIFIED", "UNTESTED"):
        if required_N <= N_PLAUSIBLE:
            robustness = "RECOVERABLE"
            flip = (f"declare collective protection with N_collective >= {required_N} "
                    f"(plausible) under mechanism {r.mechanism}")
            notes = (f"Nominally {verdict}, but a coherent ensemble of ~{required_N} "
                     "chromophores would rescue it within physical plausibility.")
        elif required_N <= N_STRETCH:
            robustness = "RECOVERABLE"
            flip = (f"declare an extreme collective mode N_collective >= {required_N} "
                    "(stretch but conceivable)")
            notes = (f"Rescuable only with an extreme coherent ensemble (N>={required_N}); "
                     "physically conceivable but unverified.")
        else:
            robustness = "FIRMLY FALSIFIED"
            flip = "none within physically allowed mechanisms"
            notes = (f"Requires N_collective >= {required_N:,} (far beyond any plausible "
                     "biological coherent ensemble). Dead under the Firmenich baseline.")
    else:
        robustness = "UNCLASSIFIED"

    return AttackReport(
        claim=r.claim_name,
        kind=r.kind,
        nominal_verdict=verdict,
        bare_ratio=bare_ratio,
        declared_pf=declared_pf,
        min_pf_to_survive=min_pf,
        protection_slack=protection_slack,
        claimed_slack=claimed_slack,
        required_N=required_N,
        robustness=robustness,
        flip_mechanism=flip,
        notes=notes,
    )


def attack_claims(claims=None) -> list:
    claims = claims if claims is not None else BUILTIN_CLAIMS
    return [attack_claim(c) for c in claims]
