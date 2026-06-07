"""Aggregations and the citation graph compute deterministic, known values."""
from patent_analytics.aggregate import aggregate
from patent_analytics.aggregate import _spearman_sign  # noqa: PLC2701
from patent_analytics.extract import PatentRecord


def _rec(doc_id, sentence, figs, cited, filing="original", material="stainless steel"):
    return PatentRecord(
        doc_id=doc_id, abstract_first_sentence=sentence, figure_count=figs,
        claim_count=10, citation_count=len(cited), cited_patents=list(cited),
        filing_type=filing, primary_material=material)


def _sample():
    return [
        _rec("patent_B_001", "A vehicle linkage.", 2, ["100", "200"]),
        _rec("patent_B_002", "A vehicle wheel.", 8, ["200", "300"], filing="continuation-in-part"),
        _rec("patent_B_003", "A polymer die.", 15, ["200", "300", "400"]),
        _rec("patent_B_004", "An optical lens.", 25, ["400"]),
        _rec("patent_B_005", "A sensor circuit.", 60, [], filing="continuation-in-part"),
        _rec("patent_B_006", "A surgical tool.", 4, ["100", "200", "300"]),
    ]


def test_topic_counts_sum_to_corpus_size():
    agg = aggregate(_sample())
    assert sum(agg["topic_counts"].values()) == 6
    assert agg["corpus_size"] == 6


def test_histogram_bins():
    agg = aggregate(_sample())
    assert agg["figure_histogram"] == {"0-5": 2, "6-10": 1, "11-20": 1, "21-50": 1, "51+": 1}


def test_citation_graph_and_most_cited():
    agg = aggregate(_sample())
    assert agg["cited_patent_to_citers_count"] == {"100": 2, "200": 4, "300": 3, "400": 2}
    assert agg["total_unique_cited_patents"] == 4
    assert agg["shared_prior_art_count"] == 4
    assert agg["max_citers_per_cited"] == 4
    assert agg["most_cited_patent_number"] == "200"


def test_cip_aggregations():
    agg = aggregate(_sample())
    assert agg["continuation_in_part_count"] == 2
    assert agg["cip_vs_noncip_mean_citations"] == {"cip_mean": 1.0, "noncip_mean": 2.25}


def test_max_figures_descriptors():
    agg = aggregate(_sample())
    assert agg["max_figure_count"] == 60
    assert agg["patent_with_max_figures"] == "patent_B_005"


def test_spearman_sign():
    assert _spearman_sign([1, 2, 3, 4], [10, 20, 30, 40]) == "positive"
    assert _spearman_sign([1, 2, 3, 4], [40, 30, 20, 10]) == "negative"
    assert _spearman_sign([1, 1, 1], [1, 2, 3]) == "none"
