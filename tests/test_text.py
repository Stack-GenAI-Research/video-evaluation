from action_semantics.text import normalize_term, normalize_text


def test_normalize_text_compacts_whitespace():
    assert normalize_text("  cut\n the   pipe ") == "cut the pipe"


def test_normalize_term_lowercases():
    assert normalize_term("Adjustable Wrench!") == "adjustable wrench"
