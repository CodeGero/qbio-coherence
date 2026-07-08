# Bio-Coherence Falsifier — Project Plan & Roadmap

Status: v0.1.0 SHIPPED to PyPI (kryptorious-qbio-coherence). Engine runs, 13 tests pass,
baseline verified at 13 fs @310K (Firmenich 2026 HEOM).

## THE THESIS
Quantum biology has been assertion-driven for 30 years. Orch-OR, "quantum
consciousness," and long-range-coherence claims are rarely checked against a real
dephasing floor. This project turns those claims into falsifiable computations:
feed it a claimed coherence time, declare (or omit) a protection mechanism, get a
verdict — SURVIVES / FALSIFIED / UNTESTED — with the failure mode and the
mandatory baseline citation. It becomes the default referee for bio-quantum claims.

## WHY IT IS UNIQUELY OURS
- The physics is already correct and current. Most "quantum biology tools" use a
  dephasing rate ~7.7e7x too slow (the old 1e6 Hz bug). We anchor to Firmenich
  2026: gamma=7.69e13 Hz, tau_coh=13 fs @310K.
- We already own the protection-model audit (ATP_QEC_DEPHASING_AUDIT.md) and the
  anti-pattern discipline (superradiance does NOT protect fidelity; factors bounded
  by literature).
- Stack is ready: PyPI + GitHub + npm + Gumroad pipeline, agent/cron infra, and a
  quantum-biophysics KB.

## ARCHITECTURE (3 phases)
PHASE 1 — PACKAGE (DONE, v0.1.0)
  - qbio_coherence: baseline.py (Firmenich floor + spin floor), protection.py
    (collective sqrt(N), non-Markovian <=5x, entropy <=50x, structured-bath ENAQT
    <=20x; superradiance exposed only as propagation, never protection),
    claims.py (built-in claim library), falsify.py (verdict engine), cli.py.
  - 13 unit tests assert the constants and verdict logic.
  - Published. CLI: `qbio-falsify check`, `baseline`, `list`.

PHASE 2 — AGENTIC RESEARCHER (next)
  - Autonomous agent ingests a paper (arXiv/PDF), extracts the coherence CLAIM
    (claimed tau, temperature, system, declared mechanism), runs the falsifier,
    emits a verdict + citation + failure mode.
  - Cron job: weekly scan arXiv for new bio-coherence claims, auto-verify against
    baseline, post a "coherence leaderboard" delta.
  - Output: a growing, public, machine-checkable registry of bio-quantum claims
    with verdicts. This is the asset labs cite.

PHASE 3 — PUBLIC STANDARD (the world-changing layer)
  - Host the leaderboard + methodology as a citable web resource (codegero.github.io
    extension or a small Flask/static site).
  - Publish a methods paper: "A Falsification Standard for Biological Quantum
    Coherence" — anchored to Firmenich, with the protection-factor bounds.
  - Push adoption: submit as a recommended verification step to journals/conferences
    in quantum biology; integrate into the SBIR / grant workflow as the mandatory
    coherence gate.
  - Monetization (secondary, per user mandate — developer tools only): premium CLI
    tier (batch claim ingestion, custom protection models, leaderboard API) behind
    the Gumroad $9 gate, like the rest of the portfolio.

## KEY TECHNICAL DECISIONS (locked)
  - Baseline is MANDATORY and immutable in code. Any new claim is compared to it.
  - Superradiance is never a protection factor (anti-pattern enforced in code + tests).
  - Protection factors are bounded and require a citation; out-of-range raises ValueError.
  - Spin claims (radical-pair/avian) use a SEPARATE floor (tau~1 us, Ritz/Hore), not
    the Firmenich electronic floor. Confusing the two regimes is a known error.
  - "No mechanism declared + exceeds 13 fs" => UNTESTED, never claimed as proof.
  - Every claim carries a claim_source for provenance/auditability.

## NEXT EXECUTABLE STEPS (autonomous, no blockers)
  1. DONE: agentic ingestion script (extract claim -> Claim dataclass -> falsify).
  2. DONE: leaderboard.json accumulation mode + CLI `board` subcommand + `ingest`.
  3. IN PROGRESS: real ingestion run — subagent pulls 2024-2026 papers via
     firecrawl_research, extracts verified quantitative claims, we run them through
     the falsifier and append to leaderboard.json (source_tag="agent").
  4. Stand up a cron (weekly) that re-runs ingestion on new arXiv papers and updates
     the board (job definition ready; created once agent output is validated).
  5. Write the methods paper draft (it is mostly already true: baseline + factors +
     verdict logic + worked examples from built-in + agent-extracted claims).
  6. Optional: GitHub repo + Gumroad premium tier hook.

## AGENTIC INGESTION CONTRACT (locked)
  - The AGENT only extracts claims (claimed tau, T, system, mechanism) and MUST
    verify each number against a real paper via inspect_paper/read_paper. It never
    invents numbers and never sets the verdict.
  - THIS package runs the deterministic verdict (falsify) and appends to the board.
    The physics stage is non-negotiable and never bypasses the Firmenich floor.
  - Claim schema (claim_from_dict): name, claimed_tau_fs, kind{electronic|spin},
    temperature_K, n_collective, non_markovian<=5, entropy<=50, structured_bath<=20,
    protection_mechanism, claim_source, notes.

## OPEN QUESTIONS / RISKS
  - Firmenich DOI (10.64898/2026.05.10.724047) is not in CrossRef — likely a
    preprint/bioRxiv-style identifier. The NUMBER (13 fs, gamma 7.69e13) is what we
    anchor to; verify the final published DOI before the methods paper goes out.
  - Protection-factor bounds are conservative; a real structured-bath/ENAQT factor
    for a specific protein needs a specific spectral-density citation, not a generic
    multiplier. The FMO built-in uses 18x with Engel 2007 + Panitchayangkoon 2010.
  - This is a STANDARD/REFEREE, not a discovery engine. The value is adoption, which
    is a distribution problem (Phase 3), not a physics problem.
  - Agent-extracted claims inherit the agent's interpretation risk. Every appended
    row carries claim_source for audit; a human/secondary-agent audit pass should
    spot-check the leaderboard before any public citation.
