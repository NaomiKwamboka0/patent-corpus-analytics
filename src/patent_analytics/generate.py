"""Deterministic synthetic patent corpus generator.

Produces realistic patent-style ``.txt`` files (header, abstract, background,
summary, detailed description, claims) for IPC category B style inventions
(operations and transport: processing, separating, mixing, printing, transport,
packaging).

Every generated patent carries a known ground truth (figure count, claim count,
the set of US patents it cites, filing type, primary material, and topic). The
generator writes the corpus plus a ``ground_truth.json`` so the extractor can be
verified against it. Generation is fully seeded and reproducible.
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Each topic maps to a keyword that is guaranteed to appear in the first
# sentence of the abstract, plus a pool of invention nouns for flavour text.
TOPIC_SPECS = {
    "medical_biological": {
        "keyword": "surgical",
        "nouns": ["surgical retractor", "implantable stent", "wound dressing applicator",
                  "blood sampling device", "diagnostic cartridge"],
    },
    "chemical_materials": {
        "keyword": "polymer",
        "nouns": ["polymer extrusion die", "catalyst support", "composite material panel",
                  "adhesive dispenser", "resin curing apparatus"],
    },
    "electronic_computing": {
        "keyword": "circuit",
        "nouns": ["sensor signal circuit", "microcontroller module", "encoder readout circuit",
                  "memory interface board", "digital image processor"],
    },
    "optical_imaging": {
        "keyword": "optical",
        "nouns": ["optical scanner head", "laser ablation assembly", "fiber optic coupler",
                  "imaging lens mount", "camera shutter mechanism"],
    },
    "manufacturing_process": {
        "keyword": "packaging machine",
        "nouns": ["packaging machine", "sheet sorter", "palletizing robot",
                  "stamping press", "molding station"],
    },
    "mechanical_structural": {
        "keyword": "vehicle",
        "nouns": ["vehicle suspension linkage", "hydraulic actuator", "conveyor turret",
                  "steering gripping apparatus", "rotor shaft assembly"],
    },
}
TOPICS = list(TOPIC_SPECS.keys())

MATERIALS = [
    "stainless steel", "polyimide film", "anodized aluminum", "Sylgard 184 elastomer",
    "titanium alloy", "high density polyethylene", "tungsten carbide", "borosilicate glass",
    "carbon fiber composite", "nitrile rubber",
]

ABSTRACT_TEMPLATES = [
    "A {keyword} based {noun} is disclosed for improving throughput and reliability.",
    "The present invention relates to a {noun} employing a {keyword} arrangement.",
    "Disclosed is a {keyword} {noun} that reduces wear during continuous operation.",
]


@dataclass
class PatentTruth:
    """Ground truth recorded at generation time, verified by the extractor."""
    doc_id: str
    topic: str
    figure_count: int
    claim_count: int
    citation_count: int
    cited_patents: list[str] = field(default_factory=list)
    filing_type: str = "original"  # "original" or "continuation-in-part"
    primary_material: str = ""


def _us_number_pool(rng: random.Random, size: int = 180) -> list[str]:
    """A shared pool of 7-digit US patent numbers, so citations overlap and
    form a real cross-corpus citation graph."""
    nums = set()
    while len(nums) < size:
        nums.add(str(rng.randint(3_000_000, 9_999_999)))
    return sorted(nums)


def _format_us_number(num: str) -> str:
    """Render 4567890 as '4,567,890' the way patents print citations."""
    return f"{int(num):,}"


def _make_patent_text(t: PatentTruth, rng: random.Random) -> str:
    spec = TOPIC_SPECS[t.topic]
    noun = rng.choice(spec["nouns"])
    abstract = rng.choice(ABSTRACT_TEMPLATES).format(keyword=spec["keyword"], noun=noun)

    lines: list[str] = []
    lines.append("United States Patent")
    lines.append(f"Patent No.: {_format_us_number(str(rng.randint(7_000_000, 9_999_999)))}")
    lines.append(f"Title: {noun.title()} And Method Of Manufacture")
    lines.append("")
    lines.append("ABSTRACT")
    lines.append(abstract + " The invention further provides a robust assembly "
                 "suitable for high volume industrial use.")
    lines.append("")

    lines.append("CROSS-REFERENCE TO RELATED APPLICATIONS" if t.filing_type ==
                 "continuation-in-part" else "FIELD OF THE INVENTION")
    if t.filing_type == "continuation-in-part":
        lines.append("This application is a continuation-in-part of a prior "
                     "co-pending application.")
    else:
        lines.append(f"The invention relates generally to a {noun}.")
    lines.append("")

    lines.append("BACKGROUND OF THE INVENTION")
    lines.append(f"Conventional approaches to the {noun} suffer from limited "
                 "durability and excessive maintenance.")
    for num in t.cited_patents:
        lines.append(f"U.S. Pat. No. {_format_us_number(num)} discloses a related "
                     "arrangement but does not address the present problem.")
    lines.append("")

    lines.append("SUMMARY OF THE INVENTION")
    lines.append(f"It is an object of the invention to provide an improved {noun} "
                 f"fabricated at least in part from {t.primary_material}.")
    lines.append("")

    lines.append("BRIEF DESCRIPTION OF THE DRAWINGS")
    for i in range(1, t.figure_count + 1):
        lines.append(f"FIG. {i} is a view of an embodiment of the {noun}.")
    lines.append("")

    lines.append("DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENTS")
    lines.append(f"Referring now to FIG. 1, the {noun} includes a main body "
                 f"formed of {t.primary_material}. With reference to FIG. "
                 f"{max(1, t.figure_count)}, the assembly is shown fully assembled.")
    lines.append("")

    lines.append("What is claimed is:")
    for i in range(1, t.claim_count + 1):
        if i == 1:
            lines.append(f"1. A {noun} comprising a body and an operative member.")
        else:
            lines.append(f"{i}. The {noun} of claim 1, further comprising an "
                         f"additional feature numbered {i}.")
    lines.append("")
    return "\n".join(lines)


def generate_corpus(out_dir: str | Path, count: int = 120, seed: int = 42) -> list[PatentTruth]:
    """Generate ``count`` patents into ``out_dir`` and write ground_truth.json.

    Returns the list of ground-truth records.
    """
    out = Path(out_dir)
    (out / "patents").mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    pool = _us_number_pool(rng)
    # A subset of "popular" prior art that many patents cite, to create hubs.
    hubs = rng.sample(pool, 12)

    truths: list[PatentTruth] = []
    for i in range(1, count + 1):
        doc_id = f"patent_B_{i:03d}"
        topic = rng.choices(TOPICS, weights=[2, 3, 3, 2, 3, 5])[0]
        # Figure counts skewed low with a long tail, to make a real histogram.
        figure_count = rng.choices(
            [rng.randint(1, 5), rng.randint(6, 10), rng.randint(11, 20),
             rng.randint(21, 50), rng.randint(51, 80)],
            weights=[35, 30, 20, 12, 3])[0]
        claim_count = rng.randint(5, 30)

        n_cites = rng.choices([0, 1, 2, 3, 5, 8, 12], weights=[8, 18, 22, 20, 16, 10, 6])[0]
        cited = set()
        for _ in range(n_cites):
            cited.add(rng.choice(hubs) if rng.random() < 0.45 else rng.choice(pool))
        cited_list = sorted(cited, key=int)

        filing_type = "continuation-in-part" if rng.random() < 0.22 else "original"
        truth = PatentTruth(
            doc_id=doc_id, topic=topic, figure_count=figure_count,
            claim_count=claim_count, citation_count=len(cited_list),
            cited_patents=cited_list, filing_type=filing_type,
            primary_material=rng.choice(MATERIALS),
        )
        text = _make_patent_text(truth, rng)
        (out / "patents" / f"{doc_id}.txt").write_text(text, encoding="utf-8")
        truths.append(truth)

    (out / "ground_truth.json").write_text(
        json.dumps([asdict(t) for t in truths], indent=2), encoding="utf-8")
    return truths


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "data"
    rows = generate_corpus(target)
    print(f"Generated {len(rows)} patents into {target}/patents")
