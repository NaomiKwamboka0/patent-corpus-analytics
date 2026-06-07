"""Topic classification follows the leftmost-wins priority chain."""
from patent_analytics.classify import TOPIC_NAMES, classify_sentence


def test_basic_buckets():
    assert classify_sentence("A surgical retractor for patients.") == "medical_biological"
    assert classify_sentence("A polymer extrusion die is disclosed.") == "chemical_materials"
    assert classify_sentence("A sensor signal circuit board.") == "electronic_computing"
    assert classify_sentence("An optical scanner head with a lens.") == "optical_imaging"
    assert classify_sentence("A packaging machine for boxes.") == "manufacturing_process"
    assert classify_sentence("A vehicle suspension linkage.") == "mechanical_structural"


def test_priority_chain_leftmost_wins():
    # Contains both 'surgical' (bucket 1) and 'vehicle' (bucket 6) -> bucket 1 wins.
    assert classify_sentence("A surgical vehicle device.") == "medical_biological"
    # Contains both 'polymer' (2) and 'circuit' (3) -> bucket 2 wins.
    assert classify_sentence("A polymer circuit.") == "chemical_materials"


def test_other_when_no_keyword():
    assert classify_sentence("A pleasant arrangement of widgets.") == "other"


def test_topic_names_has_seven():
    assert len(TOPIC_NAMES) == 7
    assert TOPIC_NAMES[-1] == "other"
