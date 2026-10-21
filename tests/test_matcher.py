import pytest

from bmpm_test.matcher import BMPMMatcher

NAMES = ["Li", "Kim", "Schmidt", "Rodriguez", "Garcia-Lopez", "Berg"]


@pytest.fixture(scope="module")
def matcher():
    m = BMPMMatcher()
    m.build_index(NAMES)
    return m


def test_encode_returns_code_set(matcher):
    assert matcher.encode("Schmidt") == frozenset({"zmit", "stzmit"})


def test_encode_is_cached(matcher):
    assert matcher.encode("Schmidt") is matcher.encode("Schmidt")


def test_phonetic_variant_matches(matcher):
    assert matcher.match("Shmit") == ["Schmidt"]


def test_unrelated_query_matches_nothing(matcher):
    assert matcher.match("Pax") == []


def test_distinct_short_names_do_not_match_each_other(matcher):
    assert "Kim" not in matcher.match("Li")


def test_matches_follow_list_order():
    m = BMPMMatcher()
    m.build_index(["Smith", "Schmidt", "Schmitt"])
    matches = m.match("Shmit")
    assert matches == [n for n in ["Smith", "Schmidt", "Schmitt"] if n in matches]
    assert "Schmidt" in matches and "Schmitt" in matches


def test_per_word_encoding_matches_single_word_overlap(matcher):
    assert "Rodriguez" in matcher.match("Hernandez Rodriguez")


def test_concat_encoding_requires_whole_name_match():
    m = BMPMMatcher(concat=True)
    m.build_index(NAMES)
    assert "Rodriguez" not in m.match("Hernandez Rodriguez")
    assert m.match("Garcia Lopes") == ["Garcia-Lopez"]


def test_exact_mode_codes_are_case_sensitive():
    m = BMPMMatcher(match_mode="exact")
    assert m.encode("Schmidt") == frozenset({"Smit", "StSmit"})


def test_name_modes_are_translated():
    assert BMPMMatcher(name_mode="ashkenazi").encode("Schmidt")


def test_invalid_modes_rejected():
    with pytest.raises(ValueError, match="name_mode"):
        BMPMMatcher(name_mode="gen")
    with pytest.raises(ValueError, match="match_mode"):
        BMPMMatcher(match_mode="fuzzy")


def test_match_before_index_raises():
    with pytest.raises(RuntimeError, match="build_index"):
        BMPMMatcher().match("Li")


def test_duplicate_names_indexed_once():
    m = BMPMMatcher()
    m.build_index(["Schmidt", "Schmidt"])
    assert m.match("Shmit") == ["Schmidt"]
