"""Extraction must reproduce the generator's ground truth from text alone."""
import json
from pathlib import Path

from patent_analytics.extract import extract_record
from patent_analytics.generate import generate_corpus


def test_extraction_matches_ground_truth(tmp_path):
    generate_corpus(tmp_path, count=40, seed=7)
    truth = {t["doc_id"]: t for t in
             json.loads((tmp_path / "ground_truth.json").read_text())}

    for path in sorted((tmp_path / "patents").glob("*.txt")):
        rec = extract_record(path)
        gt = truth[rec.doc_id]
        assert rec.figure_count == gt["figure_count"], rec.doc_id
        assert rec.claim_count == gt["claim_count"], rec.doc_id
        assert rec.citation_count == gt["citation_count"], rec.doc_id
        assert rec.cited_patents == gt["cited_patents"], rec.doc_id
        assert rec.filing_type == gt["filing_type"], rec.doc_id
        assert rec.primary_material == gt["primary_material"], rec.doc_id


def test_citation_numbers_are_digit_only(tmp_path):
    generate_corpus(tmp_path, count=10, seed=1)
    for path in (tmp_path / "patents").glob("*.txt"):
        rec = extract_record(path)
        for num in rec.cited_patents:
            assert num.isdigit() and 4 <= len(num) <= 8


def test_corpus_is_reproducible(tmp_path):
    a = generate_corpus(tmp_path / "a", count=15, seed=99)
    b = generate_corpus(tmp_path / "b", count=15, seed=99)
    assert [x.doc_id for x in a] == [x.doc_id for x in b]
    assert [x.cited_patents for x in a] == [x.cited_patents for x in b]
