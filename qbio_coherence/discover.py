"""NULLIUS discovery: free-stack literature scan (no Firecrawl, no key).

Replaces the dead Firecrawl-based Monday ingestion. Pulls recent papers from
arXiv (Atom API) and OpenAlex (JSON API) on quantum-biology coherence topics,
within a rolling window, applies a high-precision biological-context gate, and
writes a JSON list for the LLM extraction + falsify + attack stages.

Only stdlib is used so the cron has zero extra dependencies.

Usage:
    python -m qbio_coherence.discover --days 10 --out new_papers.json
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

ARXIV = "https://export.arxiv.org/api/query"
OPENALEX = "https://api.openalex.org/works"

TERMS = [
    "microtubule quantum coherence",
    "tubulin quantum",
    "biological quantum coherence",
    "photosynthetic exciton coherence",
    "radical pair compass",
    "Frohlich condensate",
    "quantum error correction biology",
    "quantum biology decoherence",
]

NS = {"a": "http://www.w3.org/2005/Atom"}
UA = {"User-Agent": "kryptorious-nullius/0.3 (research; mailto:research@kryptorious.example)"}


def _reconstruct_abstract(ai: dict | None) -> str:
    """OpenAlex stores abstracts as an inverted index {word: [positions]}.
    Reconstruct readable text by sorting words on their first occurrence."""
    if not ai:
        return ""
    slots = []
    for word, positions in ai.items():
        for p in positions:
            slots.append((p, word))
    slots.sort(key=lambda x: x[0])
    return " ".join(w for _, w in slots)


def _get(url: str, timeout: int = 30, retries: int = 4) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** (attempt + 2))  # 4s, 8s, 16s
                continue
            raise
        except Exception as e:  # URLError, socket timeout, etc.
            last = e
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 2))
                continue
            raise
    if last:
        raise last
    raise RuntimeError("unreachable")


def _is_biological(text: str) -> bool:
    """High-precision biological-context gate.

    A paper counts only if it contains BOTH (a) a quantum-relevant term AND
    (b) a specific biological term. Generic words like 'cell'/'membrane'/'dna'
    are intentionally excluded -- physics papers (cellular automata, membrane
    QED, DNA in condensed matter) trigger them and produce false positives.
    """
    t = text.lower()
    quantum = ("quantum" in t or "coherence" in t or "decohere" in t
               or "superradiance" in t or "tunnel" in t or "spin" in t)
    bio = any(k in t for k in (
        "microtubule", "tubulin", "chlorophyll", "photosynthe",
        "radical pair", "avian compass", "enzyme", "protein",
        "biological", "mitochondr", "frohlich", "orchestrated",
    ))
    return quantum and bio


def fetch_arxiv(terms, days: int, max_per: int) -> list:
    q = " OR ".join(f"all:{t}" for t in terms)
    params = {
        "search_query": q,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_per * len(terms)),
    }
    url = ARXIV + "?" + urllib.parse.urlencode(params)
    root = ET.fromstring(_get(url))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for e in root.findall("a:entry", NS):
        pub = e.find("a:published", NS).text
        dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        if dt < cutoff:
            continue
        title = " ".join(e.find("a:title", NS).text.split())
        summary = " ".join(e.find("a:summary", NS).text.split())
        if not _is_biological(title + " " + summary):
            continue
        idurl = e.find("a:id", NS).text
        out.append({
            "source": "arxiv", "id": idurl, "title": title,
            "abstract": summary, "date": pub, "url": idurl,
        })
    return out


def fetch_openalex(terms, days: int, per: int) -> list:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    out = []
    for t in terms:
        params = {
            "search": t,
            "filter": f"from_publication_date:{cutoff}",
            "per_page": str(per),
            "mailto": "research@kryptorious.example",
        }
        url = OPENALEX + "?" + urllib.parse.urlencode(params)
        try:
            data = json.loads(_get(url))
        except Exception:
            continue
        for w in data.get("results", []):
            title = w.get("title") or ""
            abstract = _reconstruct_abstract(w.get("abstract_inverted_index"))[:4000]
            if not _is_biological(title + " " + abstract):
                continue
            out.append({
                "source": "openalex",
                "id": w.get("doi") or w.get("id"),
                "title": title,
                "abstract": abstract,
                "date": w.get("publication_date") or "",
                "url": w.get("doi") or w.get("id"),
            })
    return out


def discover(days: int = 10, max_per: int = 12) -> list:
    papers = []
    try:
        papers += fetch_arxiv(TERMS, days, max_per)
    except Exception as e:  # arXiv down/throttled: keep going with OpenAlex.
        print(f"[discover] arXiv fetch failed ({e}); using OpenAlex only", file=sys.stderr)
    try:
        papers += fetch_openalex(TERMS, days, max_per)
    except Exception as e:
        print(f"[discover] OpenAlex fetch failed ({e})", file=sys.stderr)
    # Dedup on NORMALIZED TITLE, not on `id`: OpenAlex returns the same paper
    # under multiple id values (doi, openalex id, different URLs), so id-based
    # dedup leaks duplicates. Keep the first occurrence of each title.
    seen, uniq = set(), []
    for p in papers:
        key = (p.get("title") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--out", default="new_papers.json")
    ap.add_argument("--max-per", type=int, default=12)
    a = ap.parse_args()

    uniq = discover(a.days, a.max_per)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(uniq, f, indent=2)
    print(f"[discover] {len(uniq)} unique bio-relevant papers in last {a.days} days -> {a.out}")


if __name__ == "__main__":
    main()
