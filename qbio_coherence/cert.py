"""NULLIUS verdict certificate: a portable, verifiable attestation.

A researcher can attach this to a preprint or grant proposal to state, in
writing, how their claim fares against the Firmenich dephasing floor. The
certificate embeds the ledger entry hash so anyone can verify it against the
public, tamper-evident NULLIUS ledger.

This is the free, reputation-building layer. The paid certification *market* (badge
API, institutional access, crypto settlement) is intentionally out of scope for
v0.3.0 -- credibility first, monetization second.
"""

from .falsify import Report
from .ledger import Ledger, DEFAULT_LEDGER_DIR


def make_certificate(report: Report, ledger_entry=None, ledger_dir: str = None) -> str:
    """Return a markdown certificate for a falsification Report.

    If a ledger entry (LedgerEntry) is supplied, its seq + entry_hash are baked
    in so the certificate is verifiable against the public ledger.
    """
    seq = ""
    ehash = ""
    if ledger_entry is not None:
        seq = ledger_entry.seq
        ehash = ledger_entry.entry_hash

    verdict_line = {
        "SURVIVES": "SURVIVES the Firmenich 2026 dephasing floor under the declared mechanism.",
        "FALSIFIED": "FALSIFIED: exceeds what the declared (or any plausible) mechanism permits.",
        "UNTESTED": "UNTESTED: not ruled out by physics alone; requires a declared mechanism + data.",
    }.get(report.verdict, report.verdict)

    cert = f"""# NULLIUS Verdict Certificate

**Claim:** {report.claim_name}
**Verdict:** `{report.verdict}` -- {verdict_line}

## Specification
- System / kind: {report.kind}
- Temperature: {report.temperature_K} K
- Bare dephasing floor (Firmenich 2026): {report.bare_tau_fs:.1f} fs
- Declared protection mechanism: {report.mechanism}
- Total protection factor: x{report.protection_factor:.3g}
- Allowed coherence (floor x protection): {report.allowed_tau_fs:.1f} fs
- Claimed coherence: {report.claimed_tau_fs:.1f} fs
- Ratio claimed / allowed: {report.ratio:.3g}

## Failure mode
{report.failure_mode}

## Baseline
{report.baseline_source}

## Claim provenance
{report.claim_source}

## Verification
"""
    if seq != "":
        cert += (
            f"- Ledger entry: #{seq}\n"
            f"- Ledger entry hash: `{ehash}`\n"
            f"- Verify: `python -m qbio_coherence.ledger_cli verify "
            f"--ledger {ledger_dir or DEFAULT_LEDGER_DIR}`\n"
        )
    else:
        cert += (
            "- Not yet committed to the public ledger. Run "
            "`python -m qbio_coherence.ledger_cli commit` to record and obtain a "
            "verifiable entry hash.\n"
        )
    cert += (
        "\n---\n"
        "Issued by kryptorious-qbio-coherence (NULLIUS). "
        "Physics-anchored falsification, not endorsement. Experimental confirmation "
        "remains required for any surviving claim.\n"
    )
    return cert
