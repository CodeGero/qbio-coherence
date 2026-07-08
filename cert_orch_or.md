# NULLIUS Verdict Certificate

**Claim:** MT Orch-OR functional coherence (naive)
**Verdict:** `UNTESTED` -- UNTESTED: not ruled out by physics alone; requires a declared mechanism + data.

## Specification
- System / kind: electronic
- Temperature: 310.0 K
- Bare dephasing floor (Firmenich 2026): 13.0 fs
- Declared protection mechanism: none declared
- Total protection factor: x1
- Allowed coherence (floor x protection): 13.0 fs
- Claimed coherence: 1000000.0 fs
- Ratio claimed / allowed: 7.69e+04

## Failure mode
Claim exceeds the bare dephasing floor but no protection mechanism is declared. Cannot be ruled out by physics alone; requires a specific mechanism + experimental verification.

## Baseline
Firmenich et al. 2026, HEOM, gamma=7.69e13 Hz, tau~13 fs @310K

## Claim provenance
Hameroff-Penrose Orch-OR (various); unspecified mechanism

## Verification
- Ledger entry: #6
- Ledger entry hash: `d34f110dd07189e58f50a1a486345dfe8bdee571ee38d3d61d2af25c7a6a8fef`
- Verify: `python -m qbio_coherence.ledger_cli verify --ledger D:\aitest\qbio-coherence\qbio_coherence\..\nullius_ledger`

---
Issued by kryptorious-qbio-coherence (NULLIUS). Physics-anchored falsification, not endorsement. Experimental confirmation remains required for any surviving claim.
