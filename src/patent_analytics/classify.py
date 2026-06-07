"""Deterministic topic classification of a patent into one of seven buckets.

Classification is applied to the first sentence of the abstract using a priority
chain: the leftmost bucket whose keyword set matches wins. This mirrors how a
real triage step would route documents and keeps the result fully reproducible.
"""
from __future__ import annotations

from .extract import normalize

# Ordered: earlier buckets win ties on keyword overlap.
TOPIC_KEYWORDS: list[tuple[str, list[str]]] = [
    ("medical_biological", [
        "surgical", "patient", "biomedical", "therapeutic", "pharmaceutical",
        "vaccine", "diagnostic", "prosthesis", "implant", "tissue", "disease",
        "clinical", "wound dressing", "blood", "physiological", "dental", "cardiac"]),
    ("chemical_materials", [
        "polymer", "catalyst", "monomer", "molecule", "synthesis", "reagent",
        "solvent", "alloy", "ceramic", "composite material", "resin", "adhesive",
        "biodegradable", "chemical compound", "electrostatic"]),
    ("electronic_computing", [
        "circuit", "processor", "computer", "software", "digital image",
        "microcontroller", "semiconductor", "integrated circuit", "transistor",
        "memory", "algorithm", "wireless", "encoder scale", "signal processing"]),
    ("optical_imaging", [
        "optical", "lens", "laser", "imaging", "camera", "fiber optic",
        "spectroscopy", "photograph", "scanner"]),
    ("manufacturing_process", [
        "manufacturing", "packaging machine", "shredder", "sorter", "palletize",
        "method for producing", "method of producing", "process for producing",
        "casting", "stamping", "molding", "extrusion", "stapling"]),
    ("mechanical_structural", [
        "vehicle", "wheel", "axle", "engine", "transmission", "clutch", "hydraulic",
        "pneumatic", "linkage", "actuator", "pivot", "rotor", "turret", "steering",
        "suspension", "bicycle", "cart", "robotic", "gripping", "valve", "container",
        "apparatus", "device", "frame", "chassis", "shaft"]),
]
OTHER = "other"
TOPIC_NAMES = [name for name, _ in TOPIC_KEYWORDS] + [OTHER]


def classify_sentence(sentence: str) -> str:
    norm = normalize(sentence)
    for name, keywords in TOPIC_KEYWORDS:
        if any(normalize(kw) in norm for kw in keywords):
            return name
    return OTHER
