"""Protection-mechanism models for biological quantum coherence.

IMPORTANT HONESTY CONSTRAINTS (see ATP_QEC_DEPHASING_AUDIT.md and the
theoretical-biophysics-research skill anti-patterns):

1. Superradiance does NOT protect fidelity. The Dicke bright state is N times
   MORE sensitive to uncorrelated dephasing (fidelity decays as
   exp(-N*gamma_phi*t)). Superradiance only speeds up radiative PROPAGATION
   (Gamma_SR = N*gamma_0). We expose `superradiant_emission_rate` separately so
   it cannot be mistaken for a protection factor.

2. The only mechanisms that plausibly raise the effective coherence time above
   the Firmenich 13 fs floor are:
     (a) Collective-mode protection / Quantum Darwinism: common-mode rejection
         across N_coherently-coupled chromophores -> gamma_eff ~ gamma_single /
         sqrt(N_collective). (Gross & Haroche 1982; Zurek 2009.)
     (b) Non-Markovian coherence revival: stretched-exponential baths can return
         coherence; bounded ~2-5x enhancement. (Addis et al. 2014.)
     (c) Entropy-feedback stabilization: ATP-driven low-entropy maintenance;
         bounded ~5-50x but REQUIRES explicit thermodynamic justification.
         (Ahmadi et al. 2026.)
     (d) Structured-bath / ENAQT: a tuned protein spectral density that
         assists transport and extends electronic coherence; bounded ~5-20x,
         requires a specific spectral-density citation. (Engel et al. 2007;
         Panitchayangkoon et al. 2010.)

Defaults are conservative: each factor is 1.0 (no enhancement) unless the user
explicitly supplies a physically justified value.
"""

import math
from .baseline import (
    FIRMENICH_T_COH,
    T_BODY,
    SPIN_T_COH,
    bare_dephase_rate,
)


def collective_factor(n_collective: int) -> float:
    """Collective-mode protection factor (multiplicative reduction in gamma).

    gamma_eff = gamma_single / sqrt(N_collective) for the delocalized bright
    state under common-mode environmental rejection. N_collective is the number
    of coherently coupled chromophores (not total sites). Returns >= 1.
    """
    n = max(1, int(n_collective))
    return math.sqrt(n)


def non_markovian_factor(enhancement: float = 1.0) -> float:
    """Non-Markovian coherence-revival factor (multiplicative reduction in gamma).

    Must be in (1, 5] per Addis et al. 2014 for stretched-exponential baths.
    Anything > 5 is not supported by current literature and is rejected.
    """
    if enhancement <= 1.0:
        return 1.0
    if enhancement > 5.0:
        raise ValueError("non_markovian_factor > 5x is not literature-supported")
    return float(enhancement)


def entropy_feedback_factor(enhancement: float = 1.0) -> float:
    """Entropy-feedback stabilization factor (Ahmadi et al. 2026).

    Bounded ~5-50x but REQUIRES explicit thermodynamic justification (ATP budget,
    critical threshold). Default 1.0 (no enhancement). Values > 50 are rejected.
    """
    if enhancement <= 1.0:
        return 1.0
    if enhancement > 50.0:
        raise ValueError("entropy_feedback_factor > 50x is not literature-supported")
    return float(enhancement)


def structured_bath_factor(enhancement: float = 1.0) -> float:
    """Structured-spectral-density / ENAQT factor (Engel 2007; Panitchayangkoon 2010).

    A tuned protein environment that assists transport and extends electronic
    coherence. Bounded ~5-20x and REQUIRES a specific spectral-density citation.
    Values > 20 are rejected.
    """
    if enhancement <= 1.0:
        return 1.0
    if enhancement > 20.0:
        raise ValueError("structured_bath_factor > 20x is not literature-supported")
    return float(enhancement)


# --- Spin-regime (radical pair / avian compass) protection factors -----------
# The spin coherence floor (tau ~ 1 us, Ritz 2000 / Hore & Mouritsen 2016) is a
# DIFFERENT physical regime from electronic population dephasing. These factors
# are ONLY valid for kind="spin" and are cite-gated like the electronic ones.
def quantum_zeno_factor(enhancement: float = 1.0) -> float:
    """Spin protection via the quantum Zeno effect: frequent measurement/projective
    coupling to a chiral protein environment freezes dephasing. Bounded ~2-50x.
    (Kritman et al.; arXiv:2505.01519 chirality-bolstered Zeno, 2025.)
    REQUIRES an explicit citation. Values > 50 are rejected."""
    if enhancement <= 1.0:
        return 1.0
    if enhancement > 50.0:
        raise ValueError("quantum_zeno_factor > 50x is not literature-supported")
    return float(enhancement)


def hyperfine_protection_factor(enhancement: float = 1.0) -> float:
    """Spin protection via tuned anisotropic hyperfine couplings that suppress
    dephasing (the 'quantum needle' of Hore 2016). Bounded ~2-10x. Values > 10
    are rejected."""
    if enhancement <= 1.0:
        return 1.0
    if enhancement > 10.0:
        raise ValueError("hyperfine_protection_factor > 10x is not literature-supported")
    return float(enhancement)


def superradiant_emission_rate(gamma_0: float, n_sites: int) -> float:
    """Radiative PROPAGATION speedup only. NOT a coherence-protection factor.

    Gamma_SR = N * gamma_0 for the collective bright state. Use this to compute
    signal propagation speed, never to justify extended coherence.
    """
    return float(gamma_0) * max(1, int(n_sites))


def effective_dephase_rate(
    temperature_K: float = T_BODY,
    kind: str = "electronic",
    n_collective: int = 1,
    non_markovian: float = 1.0,
    entropy: float = 1.0,
    structured_bath: float = 1.0,
    quantum_zeno: float = 1.0,
    hyperfine: float = 1.0,
) -> float:
    """Effective dephasing rate after protection mechanisms.

    Electronic regime: gamma_eff = bare / (collective * nm * entropy * structured_bath).
    Spin regime:      gamma_eff = bare / (collective * nm * zeno * hyperfine).
    """
    bare = bare_dephase_rate(temperature_K) if kind == "electronic" else (
        1.0 / SPIN_T_COH
    )
    if kind == "spin":
        total = (
            collective_factor(n_collective)
            * non_markovian_factor(non_markovian)
            * quantum_zeno_factor(quantum_zeno)
            * hyperfine_protection_factor(hyperfine)
        )
    else:
        total = (
            collective_factor(n_collective)
            * non_markovian_factor(non_markovian)
            * entropy_feedback_factor(entropy)
            * structured_bath_factor(structured_bath)
        )
    return bare / total


def effective_coherence_time(
    temperature_K: float = T_BODY,
    kind: str = "electronic",
    n_collective: int = 1,
    non_markovian: float = 1.0,
    entropy: float = 1.0,
    structured_bath: float = 1.0,
    quantum_zeno: float = 1.0,
    hyperfine: float = 1.0,
) -> float:
    """Inverse of effective_dephase_rate."""
    return 1.0 / effective_dephase_rate(
        temperature_K, kind, n_collective, non_markovian, entropy,
        structured_bath, quantum_zeno, hyperfine,
    )


def total_protection_factor(
    n_collective: int = 1,
    non_markovian: float = 1.0,
    entropy: float = 1.0,
    structured_bath: float = 1.0,
    quantum_zeno: float = 1.0,
    hyperfine: float = 1.0,
    kind: str = "electronic",
) -> float:
    if kind == "spin":
        return (
            collective_factor(n_collective)
            * non_markovian_factor(non_markovian)
            * quantum_zeno_factor(quantum_zeno)
            * hyperfine_protection_factor(hyperfine)
        )
    return (
        collective_factor(n_collective)
        * non_markovian_factor(non_markovian)
        * entropy_feedback_factor(entropy)
        * structured_bath_factor(structured_bath)
    )
