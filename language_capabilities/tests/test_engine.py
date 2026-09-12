"""
test_engine.py

Unit tests for engine.py's row-mapping behavior — added alongside the
paraphrase-en capability, which exercises two things the original 6 gloss
capabilities never did: a plain_lines (monolingual) input, and an "Original"
output column populated from the source line rather than the LLM response.
"""

import os
import tempfile

from language_capabilities import engine
from language_capabilities.capabilities import CATALOG


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, responses):
        self._responses = iter(responses)

    def create(self, **kwargs):
        return _FakeResponse(next(self._responses))


class _FakeClient:
    def __init__(self, responses):
        self.chat = type("_Chat", (), {"completions": _FakeCompletions(responses)})()


def test_paraphrase_capability_is_registered_with_expected_shape():
    capability = CATALOG["paraphrase-en"]
    assert capability.input_format == "plain_lines"
    assert capability.output_columns == ["Original", "Paraphrase"]
    assert capability.include_passthrough_headers is False


def test_run_capability_produces_one_row_per_line_with_original_column():
    capability = CATALOG["paraphrase-en"]
    responses = [
        '[{"paraphrase": "A rewritten first line."}]',
        '[{"paraphrase": "A rewritten second line."}]',
    ]
    client = _FakeClient(responses)

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "sample.txt")
        output_path = os.path.join(tmp_dir, "out.csv")
        with open(input_path, "w", encoding="utf-8") as f:
            f.write("First original line.\nSecond original line.\n")

        run = engine.run_capability(client, capability, input_path, output_path)

        assert run.error_count == 0
        assert run.total_lines == 2

        with open(output_path, encoding="utf-8-sig") as f:
            rows = [line.strip().split(",", 1) for line in f.read().splitlines()]

    # Header + exactly one row per input line (no passthrough header rows).
    assert rows[0] == ["Original", "Paraphrase"]
    assert len(rows) == 3
    assert rows[1][0] == "First original line."
    assert rows[2][0] == "Second original line."
