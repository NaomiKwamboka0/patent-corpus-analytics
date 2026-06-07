"""End-to-end orchestration: extract -> classify -> aggregate -> output.json."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .aggregate import aggregate
from .classify import classify_sentence
from .extract import extract_corpus


def build_output(patents_dir: str | Path) -> dict:
    records = extract_corpus(patents_dir)
    if not records:
        raise FileNotFoundError(f"No .txt patents found in {patents_dir}")
    patents = []
    for r in records:
        row = asdict(r)
        row["topic"] = classify_sentence(r.abstract_first_sentence)
        row.pop("abstract_first_sentence", None)
        patents.append(row)
    return {"patents": patents, "aggregations": aggregate(records)}


def run_pipeline(patents_dir: str | Path, out_path: str | Path) -> dict:
    output = build_output(patents_dir)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output
