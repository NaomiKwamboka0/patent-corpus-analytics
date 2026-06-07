"""Patent corpus analytics: generate, extract, classify, and aggregate a corpus
of patent documents into a structured analytics report."""
from .aggregate import aggregate, build_citation_graph
from .classify import classify_sentence
from .extract import PatentRecord, extract_corpus, extract_record
from .generate import generate_corpus
from .pipeline import build_output, run_pipeline

__version__ = "0.1.0"
__all__ = [
    "generate_corpus", "extract_record", "extract_corpus", "PatentRecord",
    "classify_sentence", "aggregate", "build_citation_graph",
    "build_output", "run_pipeline",
]
