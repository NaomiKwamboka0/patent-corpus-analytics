"""Corpus-level analytics over the per-patent records.

Computes descriptive statistics, group-by means, a figure-vs-citation rank
correlation, a binned histogram, and the full cross-corpus citation graph
(who cites whom, and the most-cited prior art). Everything is deterministic.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict

import numpy as np

from .classify import TOPIC_NAMES, classify_sentence
from .extract import PatentRecord


def _rank(values: list[float]) -> list[float]:
    """Average-rank of each value (ties share the mean rank)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1  # 1-based average rank
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman_sign(xs: list[float], ys: list[float], threshold: float = 0.1) -> str:
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return "none"
    rho = float(np.corrcoef(_rank(xs), _rank(ys))[0, 1])
    if rho >= threshold:
        return "positive"
    if rho <= -threshold:
        return "negative"
    return "none"


def _histogram(values: list[int]) -> dict[str, int]:
    bins = {"0-5": 0, "6-10": 0, "11-20": 0, "21-50": 0, "51+": 0}
    for v in values:
        if v <= 5:
            bins["0-5"] += 1
        elif v <= 10:
            bins["6-10"] += 1
        elif v <= 20:
            bins["11-20"] += 1
        elif v <= 50:
            bins["21-50"] += 1
        else:
            bins["51+"] += 1
    return bins


def _mean_by_topic(records, topics, key, round_to=2):
    groups = defaultdict(list)
    for r, t in zip(records, topics):
        groups[t].append(getattr(r, key))
    return {t: (round(statistics.mean(groups[t]), round_to) if groups[t] else 0.0)
            for t in TOPIC_NAMES}


def _total_by_topic(records, topics, key):
    groups = defaultdict(int)
    for r, t in zip(records, topics):
        groups[t] += getattr(r, key)
    return {t: int(groups.get(t, 0)) for t in TOPIC_NAMES}


def _max_per_topic(records, topics, key):
    best: dict[str, tuple] = {}
    for r, t in zip(records, topics):
        val = getattr(r, key)
        cur = best.get(t)
        if cur is None or val > cur[0] or (val == cur[0] and r.doc_id < cur[1]):
            best[t] = (val, r.doc_id)
    return {t: best[t][1] for t in sorted(best)}


def build_citation_graph(records: list[PatentRecord]) -> dict[str, int]:
    """Map each cited US patent number -> number of corpus patents citing it."""
    counter: Counter[str] = Counter()
    for r in records:
        for num in set(r.cited_patents):
            counter[num] += 1
    return dict(sorted(counter.items(), key=lambda kv: int(kv[0])))


def aggregate(records: list[PatentRecord]) -> dict:
    topics = [classify_sentence(r.abstract_first_sentence) for r in records]
    figures = [r.figure_count for r in records]
    cites = [r.citation_count for r in records]

    fig_median = statistics.median(figures)
    cite_median = statistics.median(cites)

    topic_counts = Counter(topics)
    topic_counts = {t: int(topic_counts.get(t, 0)) for t in TOPIC_NAMES}

    max_fig = max(figures)
    patent_with_max = min(r.doc_id for r in records if r.figure_count == max_fig)

    graph = build_citation_graph(records)
    shared = {k: v for k, v in graph.items() if v >= 2}
    max_citers = max(graph.values()) if graph else 0
    most_cited = ""
    if graph:
        most_cited = min((k for k, v in graph.items() if v == max_citers), key=int)

    mean_fig_by_topic = _mean_by_topic(records, topics, "figure_count")
    nonempty = {t: m for t, m in mean_fig_by_topic.items() if topic_counts[t] > 0}
    topic_top = min((t for t in nonempty if nonempty[t] == max(nonempty.values())))

    by_cite_desc = sorted(records, key=lambda r: (-r.citation_count, r.doc_id))
    cip = [r for r in records if r.filing_type == "continuation-in-part"]
    noncip = [r for r in records if r.filing_type != "continuation-in-part"]

    def _mean(rs, key):
        return round(statistics.mean([getattr(r, key) for r in rs]), 2) if rs else 0.0

    return {
        "corpus_size": len(records),
        "topic_counts": topic_counts,
        "max_figure_count": int(max_fig),
        "patent_with_max_figures": patent_with_max,
        "patents_above_median_figures": int(sum(1 for f in figures if f > fig_median)),
        "total_unique_cited_patents": len(graph),
        "continuation_in_part_count": len(cip),
        "mean_figures_by_topic": mean_fig_by_topic,
        "top_3_patents_by_citations": [r.doc_id for r in by_cite_desc[:3]],
        "cip_vs_noncip_mean_citations": {
            "cip_mean": _mean(cip, "citation_count"),
            "noncip_mean": _mean(noncip, "citation_count"),
        },
        "topic_with_highest_mean_figures": topic_top,
        "figure_count_stdev": round(statistics.pstdev(figures), 2),
        "citation_count_stdev": round(statistics.pstdev(cites), 2),
        "citation_count_mean": round(statistics.mean(cites), 2),
        "citation_count_median": round(cite_median, 2),
        "figure_citation_rank_correlation_sign": _spearman_sign(figures, cites),
        "mean_citations_by_topic": _mean_by_topic(records, topics, "citation_count"),
        "total_citations_by_topic": _total_by_topic(records, topics, "citation_count"),
        "count_high_figure_high_cite": int(sum(
            1 for r in records
            if r.figure_count > fig_median and r.citation_count > cite_median)),
        "figure_histogram": _histogram(figures),
        "patent_with_max_figures_per_topic": _max_per_topic(records, topics, "figure_count"),
        "count_metal_material": int(sum(
            1 for r in records
            if any(m in r.primary_material for m in ("steel", "aluminum", "titanium",
                                                     "alloy", "carbide")))),
        "shared_prior_art_count": len(shared),
        "cited_patent_to_citers_count": graph,
        "max_citers_per_cited": int(max_citers),
        "most_cited_patent_number": most_cited,
    }
