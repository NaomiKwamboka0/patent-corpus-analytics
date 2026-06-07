"""Render summary charts from an aggregations dict (headless Agg backend)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _save(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def topic_distribution(agg: dict, out: str | Path) -> Path:
    counts = {k: v for k, v in agg["topic_counts"].items() if v > 0}
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(list(counts.keys()), list(counts.values()), color="#3b6fb6")
    ax.set_title("Patents per topic bucket")
    ax.set_ylabel("count")
    ax.tick_params(axis="x", rotation=30)
    for lbl in ax.get_xticklabels():
        lbl.set_ha("right")
    _save(fig, Path(out))
    return Path(out)


def figure_histogram(agg: dict, out: str | Path) -> Path:
    hist = agg["figure_histogram"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(list(hist.keys()), list(hist.values()), color="#5aa469")
    ax.set_title("Distribution of figure counts")
    ax.set_xlabel("figures per patent")
    ax.set_ylabel("number of patents")
    _save(fig, Path(out))
    return Path(out)


def top_cited(agg: dict, out: str | Path, top_n: int = 10) -> Path:
    graph = agg["cited_patent_to_citers_count"]
    items = sorted(graph.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(labels[::-1], vals[::-1], color="#c1666b")
    ax.set_title(f"Top {top_n} most-cited prior-art patents")
    ax.set_xlabel("number of citing patents in corpus")
    _save(fig, Path(out))
    return Path(out)


def render_all(agg: dict, charts_dir: str | Path) -> list[Path]:
    d = Path(charts_dir)
    return [
        topic_distribution(agg, d / "topic_distribution.png"),
        figure_histogram(agg, d / "figure_histogram.png"),
        top_cited(agg, d / "top_cited_prior_art.png"),
    ]
