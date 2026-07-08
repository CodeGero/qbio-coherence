"""Mandatory dephasing baseline for biological quantum-coherence claims.

Firmenich et al. (2026), "Beyond Redfield: Thermodynamic Bounds and
Non-Perturbative Quantum Dynamics in Tubulin Networks"
(doi:10.64898/2026.05.10.724047).

A 30 ps HEOM trajectory on the 1JFF tryptophan network at 310 K yields a
conservative electronic coherence time tau_coh ~ 13 fs, corresponding to a
dephasing rate gamma_dephase = 1/tau_coh = 7.69e13 Hz. This is the single-site
(bare) electronic dephasing floor in a realistic protein/aqueous environment.

ANY claim of functional biological quantum coherence extending beyond this MUST
specify a protection mechanism, quantify the enhancement factor, and compare to
this baseline. "The protein environment is special" is not sufficient -- the
Firmenich calculation already incorporates a realistic protein environment.
"""

import numpy as np

# --- Firmenich et al. (2026) HEOM baseline (single-Trp electronic, 310 K) ---
FIRMENICH_GAMMA_DEPHASE = 7.69e13  # Hz  (dephasing rate)
FIRMENICH_T_COH = 1.0 / FIRMENICH_GAMMA_DEPHASE  # s  = 1.30e-14 s = 13 fs
T_BODY = 310.0  # K

# --- Spin-coherence baseline (radical-pair / avian compass) ---
# Different physical regime: spin dephasing under low zero-field splitting and
# hyperfine protection, NOT electronic population dephasing. Conservative
# spin-coherence time ~ 1 us (gamma ~ 1e6 Hz). Source: Ritz et al. 2000;
# Hore & Mouritsen 2016 (annual review). Used ONLY for kind="spin" claims.
SPIN_GAMMA_BARE = 1.0e6  # Hz  -> tau ~ 1 us
SPIN_T_COH = 1.0 / SPIN_GAMMA_BARE

# --- Physical constants (CODATA 2018) ---
H_BAR = 1.054571817e-34  # J*s
K_B = 1.380649e-23       # J/K


def bare_coherence_time(temperature_K: float = T_BODY) -> float:
    """Single-site electronic coherence time at a given temperature.

    Honest high-temperature scaling: gamma ~ T (Ohmic-like), so
    tau(T) = tau_310 * (310 / T). At 310 K this recovers the Firmenich 13 fs.
    """
    return FIRMENICH_T_COH * (T_BODY / float(temperature_K))


def bare_dephase_rate(temperature_K: float = T_BODY) -> float:
    """Inverse of bare_coherence_time."""
    return 1.0 / bare_coherence_time(temperature_K)
