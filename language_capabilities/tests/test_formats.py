"""
test_formats.py (T026)

Unit tests for the 3 input-format parsers.
"""

from language_capabilities import formats

TWO_LINE_SAMPLE = """[Greeting]
A: 你好
B: Hello

A: 谢谢
B: Thank you
"""


def test_two_line_parses_section_and_lines():
    entries = formats.parse_two_line(TWO_LINE_SAMPLE)
    assert entries[0] == {"type": "section", "name": "Greeting"}
    line_entries = [e for e in entries if e["type"] == "line"]
    assert len(line_entries) == 2
    assert line_entries[0]["target"] == "你好"
    assert line_entries[0]["english"] == "Hello"
    assert line_entries[0]["romanization"] is None


def test_two_line_ignores_a_line_with_no_following_b_line():
    entries = formats.parse_two_line("A: orphaned\nC: not a B line\n")
    assert [e for e in entries if e["type"] == "line"] == []


THREE_LINE_WITH_ROMANIZATION = """A: 저는
P: jeoneun
B: I (topic)
"""

THREE_LINE_FALLBACK_TO_TWO = """A: 안녕
B: Hello
"""


def test_three_line_parses_triplet_with_romanization():
    entries = formats.parse_three_line(THREE_LINE_WITH_ROMANIZATION)
    assert len(entries) == 1
    assert entries[0]["target"] == "저는"
    assert entries[0]["romanization"] == "jeoneun"
    assert entries[0]["english"] == "I (topic)"


def test_three_line_falls_back_to_pair_without_p_line():
    entries = formats.parse_three_line(THREE_LINE_FALLBACK_TO_TWO)
    assert len(entries) == 1
    assert entries[0]["target"] == "안녕"
    assert entries[0]["romanization"] is None
    assert entries[0]["english"] == "Hello"


def test_csv_rows_parses_header_and_rows(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "romanization,korean,translation\nannyeong,안녕,hello\n", encoding="utf-8"
    )
    entries = formats.parse_csv_rows(str(csv_path), target_field="korean")
    assert len(entries) == 1
    assert entries[0]["target"] == "안녕"
    assert entries[0]["english"] == "hello"


def test_csv_rows_falls_back_to_english_column_and_position_one(tmp_path):
    csv_path = tmp_path / "sample2.csv"
    csv_path.write_text("col0,spanish,english\nx,Hola,Hello\n", encoding="utf-8")
    entries = formats.parse_csv_rows(str(csv_path), target_field="")
    assert len(entries) == 1
    assert entries[0]["target"] == "Hola"  # falls back to column index 1
    assert entries[0]["english"] == "Hello"


def test_csv_rows_returns_empty_list_for_empty_file(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")
    assert formats.parse_csv_rows(str(csv_path)) == []


PLAIN_LINES_SAMPLE = """[Notes]
The quick brown fox jumps over the lazy dog.

She sells seashells by the seashore.
"""


def test_plain_lines_parses_section_and_lines_with_no_translation():
    entries = formats.parse_plain_lines(PLAIN_LINES_SAMPLE)
    assert entries[0] == {"type": "section", "name": "Notes"}
    line_entries = [e for e in entries if e["type"] == "line"]
    assert len(line_entries) == 2
    assert line_entries[0]["target"] == "The quick brown fox jumps over the lazy dog."
    assert line_entries[0]["english"] is None
    assert line_entries[0]["romanization"] is None


def test_plain_lines_skips_blank_lines():
    entries = formats.parse_plain_lines("\n\nOnly one real line\n\n\n")
    assert len(entries) == 1
    assert entries[0]["target"] == "Only one real line"
