# NULLIUS: An Adversarial Falsification Protocol for Biological Quantum-Coherence Claims

**Status:** Preprint manuscript — staged for submission. Not yet posted.
**Corresponding author:** Kryptorious Quantum Biosciences (dev@kryptorious.com)
**Code:** https://github.com/CodeGero/qbio-coherence  ·  **Live board:** https://codegero.github.io/qbio-coherence
**License:** MIT (code); CC-BY (this manuscript)

---

## Abstract

Quantum-biology coherence claims are frequently published without a quantitative
test against the known dephasing limits of warm, wet biomatter. We present NULLIUS,
an open computational protocol that anchors every biological quantum-coherence claim
to a single, reproducible dephasing floor — the Firmenich et al. (2026) HEOM result
for the tubulin tryptophan network: γ = 7.69 × 10¹³ Hz, τ_coh = 13 fs at 310 K — and
emits a structured verdict (SURVIVES / FALSIFIED / UNTESTED) with the required
protection mechanism made explicit. Each verdict is recorded in a hash-chained,
tamper-evident ledger, and every claim is subjected to an adversarial sensitivity
swarm that reports the minimum protection factor needed to survive. We apply the
protocol to a reference library of six canonical claims and show that (i) claims
exceeding the floor without a declared, quantified mechanism are FALSIFIED, not
merely "untested," and (ii) claims that survive do so only under a specific, auditable
protection assumption. NULLIUS is offered as shared infrastructure: any lab can run
`nullius check` on its own claim and obtain a verifiable certificate.

---

## 1. Motivation

The replication crisis has shown that fields with weak pre-registration and weak
falsification norms accumulate false positives. Quantum biology is structurally
vulnerable: the distinction between a real, functional coherence and a
decoherence-limited artifact is subtle, and the relevant dephasing literature (HEOM,
Redfield, NMR relaxometry) is not routinely applied by claimants. The result is a
literature where coherence times are asserted, implied, or assumed without a
consistency check against the physical floor.

NULLIUS attacks this directly. It does not assert that biological quantum coherence
is absent — it asserts that *any* coherence claim must be tested against the
dephasing floor, and that the mechanism lifting the claim above the floor must be
named and quantified.

## 2. The dephasing floor (baseline)

The protocol's reference is Firmenich et al. (2026), a non-perturbative HEOM
calculation on the 1JFF tryptophan network at physiological temperature, giving:

- γ_dephase = 7.69 × 10¹³ Hz
- τ_coh = 13 fs at 310 K

**Honesty note (load-bearing).** This baseline is a **PREPRINT** (publisher: openRxiv;
type: posted-content; dated 2026-05-13), not a peer-reviewed journal article. It is
reproducible and widely cited, but if a replication moves the floor, every stored
verdict must be re-verified. The ledger is therefore re-based, not immutable: when
the baseline changes, all entries are re-tested and the chain is extended with a
rebase marker. We do not silently alter past verdicts.

For spin claims (radical-pair magnetoreception), a separate, longer baseline applies
(Ritz et al. 2000; Hore & Mouritsen 2016): τ ~ 1 µs. Electronic and spin regimes are
never conflated.

## 3. Verdict logic

For a claim with declared coherence time τ_c, temperature T, and protection factors
(collective N, non-Markovian, entropy, structured bath, quantum-Zeno, hyperfine), the
protocol computes the allowed coherence time

    τ_allowed = τ_floor(T) × Π(protection factors)

and compares τ_c to τ_allowed × SURVIVE_MARGIN (margin = 2×, to absorb experimental
error).

- **SURVIVES** if τ_c ≤ τ_allowed × margin *and* a mechanism is declared. Physics-consistent; still requires experimental proof.
- **FALSIFIED** if τ_c exceeds what the declared mechanism can permit, *or* if τ_c exceeds the bare floor with no mechanism declared. No mechanism + exceed floor = physically ruled out.
- **UNTESTED** is reserved for claims with missing information that prevents a decision (e.g. no coherence time stated and no mechanism), not for claims that merely "might" have a hidden rescue.

The key correction in this work: a no-mechanism claim that exceeds the floor is
**FALSIFIED**, not "untested." "Untested" previously implied physics could not rule
it out; in fact the floor alone rules it out. This closes a loophole that let
unsupported microtubule-coherence claims survive by default.

## 4. Adversarial sensitivity swarm

Each claim is stress-tested by probing the parameter range of every declared
protection factor. The swarm reports:

- bare ratio (τ_c / τ_floor),
- declared protection factor,
- minimum protection factor needed to survive,
- protection slack (how much headroom the declared mechanism has),
- required N_collective if collective protection is invoked,
- robustness classification: ROBUST / FRAGILE / RECOVERABLE / FIRMLY FALSIFIED.

This converts "the claim is falsified" into "the claim is falsified *unless* you can
demonstrate a protection factor of at least ×N with mechanism M" — a constructive,
testable statement.

## 5. Tamper-evident ledger

Every verdict is appended to a hash-chained JSON ledger:

    entry_hash_i = SHA256(prev_hash_{i-1} || canonical(payload_i))

Altering any past verdict breaks the chain from that point forward; `verify()`
detects the first broken index. This makes the scientific record auditable: a
skeptic can clone the repo, run `nullius verify`, and confirm no verdict was
retroactively edited.

## 6. Reference results

Applied to six canonical claims:

| Claim | Verdict |
|---|---|
| MT bare electronic (Firmenich null) | FALSIFIED |
| MT Orch-OR functional coherence (naive, no mechanism) | FALSIFIED |
| MT collective-mode protection (N=1000) | SURVIVES |
| Avian compass (radical pair, spin) | SURVIVES |
| Photosynthetic EET (FMO) | SURVIVES |
| Collagen-piezo proton tunneling (Stark-shifted) | SURVIVES |

The two FALSIFIED entries are the honest null (the floor itself) and the naive
Orch-OR claim (coherence asserted without a quantified lift). The three SURVIVES
entries each name the mechanism that permits them.

## 7. Usage (third-party)

```bash
pip install kryptorious-qbio-coherence
# falsify your own claim:
python -m qbio_coherence.ledger_cli check \
  --name "My MT claim" --tau 400 --kind electronic \
  --n_collective 1000 --protection_mechanism "collective 1/sqrt N" \
  --claim_source "MyPaper DOI"
# -> prints verdict + failure mode; FALSIFIED writes a pending draft
```

## 8. Limitations

1. The baseline is a preprint. Rebase-on-replication is implemented but untested against a moved floor.
2. Extraction of claims from paper text is currently manual/external (the weekly cron reads abstracts). Full-text extraction would thicken the corpus but requires API access not always available.
3. Protection-factor bounds (collective √N, non-Markovian ≤5×, entropy ≤50×, structured ≤20×) are literature-anchored heuristics, not derived first principles for every system.
4. NULLIUS screens consistency; it does not prove function. A SURVIVES verdict is necessary, not sufficient.

## 9. Conclusion

NULLIUS makes the falsification step in quantum-biology coherence claims automatic,
public, and auditable. It is deliberately conservative: it never asserts a mechanism
works, only whether a claim is consistent with the dephasing floor under the
mechanism its author declares. We release it as infrastructure and invite the field
to falsify — or be falsified.

---

## References

- Firmenich et al. (2026). *Beyond Redfield: Thermodynamic Bounds and Non-Perturbative Quantum Dynamics in Tubulin Networks.* openRxiv. DOI: 10.64898/2026.05.10.724047.
- Ritz et al. (2000). *A model for photoreceptor-based magnetoreception in birds.* Biophys. J.
- Hore & Mouritsen (2016). *Shedding light on a mystery: the radical-pair mechanism of avian magnetoreception.* Annu. Rev. Biophys.
- Engel et al. (2007). *Evidence for wavelike energy transfer through quantum coherence in photosynthetic systems.* Nature.
- Gross & Haroche (1982); Zurek (2009). Collective protection / Quantum Darwinism.
