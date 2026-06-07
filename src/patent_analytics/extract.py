"""Structured extraction from raw patent text.

Each ``.txt`` patent is parsed into a :class:`PatentRecord` with the metrics the
corpus analytics are built on. The extractor is intentionally independent of the
generator: it works from text alone, using regexes, so it can be pointed at real
patent dumps as well as the synthetic corpus.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# US patent citation, e.g. "U.S. Pat. No. 4,567,890" or "US Patent No 4567890".
US_CITATION_RE = re.compile(r"U\.?\s?S\.?\s+Pat(?:\.|ent)\s+No\.?\s*([\d,]+)", re.IGNORECASE)
FIG_RE = re.compile(r"\bFIG\.?\s*(\d+)", re.IGNORECASE)
CLAIM_RE = re.compile(r"^\s*(\d+)\.\s", re.MULTILINE)
CIP_RE = re.compile(r"continuation-in-part|CROSS[-\s]?REFERENCE TO RELATED APPLICATION", re.IGNORECASE)

MATERIALS = [
    "stainless steel", "polyimide film", "anodized aluminum", "Sylgard 184 elastomer",
    "titanium alloy", "high density polyethylene", "tungsten carbide", "borosilicate glass",
    "carbon fiber composite", "nitrile rubber",
]


@dataclass
class PatentRecord:
    doc_id: str
    abstract_first_sentence: str
    figure_count: int
    claim_count: int
    citation_count: int
    cited_patents: list[str] = field(default_factory=list)
    filing_type: str = "original"
    primary_material: str = ""


def normalize(text: str) -> str:
    """NFKD normalise, collapse whitespace, lowercase. Used for fuzzy matching."""
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _section(text: str, header: str) -> str:
    """Return the body following an all-caps section header up to the next header."""
    lines = text.splitlines()
    headers = {"ABSTRACT", "CROSS-REFERENCE TO RELATED APPLICATIONS",
               "FIELD OF THE INVENTION", "BACKGROUND OF THE INVENTION",
               "SUMMARY OF THE INVENTION", "BRIEF DESCRIPTION OF THE DRAWINGS",
               "DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS",
               "WHAT IS CLAIMED IS:"}
    out, capturing = [], False
    for line in lines:
        stripped = line.strip()
        if stripped.upper() == header.upper():
            capturing = True
            continue
        if capturing and stripped.upper() in headers:
            break
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


def _first_sentence(block: str) -> str:
    block = block.strip()
    if not block:
        return ""
    m = re.search(r"(.+?[.!?])(\s|$)", block, re.DOTALL)
    return (m.group(1) if m else block).strip()


def _cited_numbers(text: str) -> list[str]:
    """Distinct US patent numbers (digits only, length 4 to 8), corpus-comparable."""
    found = set()
    for raw in US_CITATION_RE.findall(text):
        digits = raw.replace(",", "")
        if 4 <= len(digits) <= 8 and digits.isdigit():
            found.add(digits)
    return sorted(found, key=int)


def _claim_count(text: str) -> int:
    claims = _section(text, "What is claimed is:")
    nums = [int(n) for n in CLAIM_RE.findall(claims)]
    return max(nums) if nums else 0


def _figure_count(text: str) -> int:
    nums = [int(n) for n in FIG_RE.findall(text)]
    return max(nums) if nums else 0


def _primary_material(text: str) -> str:
    norm = normalize(text)
    best, best_pos = "", len(norm) + 1
    for mat in MATERIALS:
        pos = norm.find(normalize(mat))
        if pos != -1 and pos < best_pos:
            best, best_pos = mat, pos
    return best


def extract_record(path: str | Path) -> PatentRecord:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    cited = _cited_numbers(text)
    return PatentRecord(
        doc_id=path.stem,
        abstract_first_sentence=_first_sentence(_section(text, "ABSTRACT")),
        figure_count=_figure_count(text),
        claim_count=_claim_count(text),
        citation_count=len(cited),
        cited_patents=cited,
        filing_type="continuation-in-part" if CIP_RE.search(text) else "original",
        primary_material=_primary_material(text),
    )


def extract_corpus(patents_dir: str | Path) -> list[PatentRecord]:
    paths = sorted(Path(patents_dir).glob("*.txt"))
    return [extract_record(p) for p in paths]
