# NULLIUS — Adversarial Truth Ledger for Biological Quantum-Coherence Claims

**A computational falsification engine that holds quantum-biology coherence claims to a fixed, reproducible dephasing floor — and publishes the verdicts in a tamper-evident public ledger.**

> Live board: https://codegero.github.io/qbio-coherence

## What it does
- Takes a claimed biological quantum-coherence time and compares it to the **Firmenich et al. 2026 HEOM dephasing floor** (γ = 7.69×10¹³ Hz, τ_coh = 13 fs @ 310 K).
- Emits **SURVIVES / FALSIFIED / UNTESTED**, with the protection mechanism and factor shown for each claim.
- Records every verdict in a **hash-chained, tamper-evident ledger**.
- Runs an **adversarial sensitivity swarm** ("attack") that probes parameter ranges and classifies claims as ROBUST / FRAGILE / RECOVERABLE / FIRMLY FALSIFIED.
- Generates a **public HTML board** (this repo's GitHub Pages site).

## Honesty notice
The dephasing floor is a **PREPRINT** (openRxiv, posted-content, 2026-05-13), not a peer-reviewed article. It is reproducible and widely cited, but if a replication moves the floor, every stored verdict must be re-verified. Verdicts are **screening judgments**, not settled fact.

## Install
```
pip install kryptorious-qbio-coherence
```

## Quickstart
```
python -m qbio_coherence.ledger_cli discover --days 7      # scan arXiv+OpenAlex (free, no key)
python -m qbio_coherence.ledger_cli attack --json atk.json # adversarial sensitivity swarm
python -m qbio_coherence.ledger_cli commit                 # seed the ledger from verdicts
python -m qbio_coherence.ledger_cli verify                 # LEDGER VALID?
python -m qbio_coherence.ledger_cli board --out docs/index.html
```

## Why
Quantum biology is haunted by claims that exceed known decoherence limits. NULLIUS makes the falsification step automatic, public, and auditable — so a coherence claim that survives has actually been *tested*, and a claim that falls is *shown why*.

## License
MIT
