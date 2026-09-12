# Adding a new capability

A "capability" is one prompt + input format + output-column bundle — what used to require copying an entire script and a `language.py`-style config file. Adding one is **one new file, zero engine changes** (FR-004).

## Steps

1. Copy `capabilities/example_gloss.py` to a new file in `language_capabilities/capabilities/`, e.g. `capabilities/german_gloss.py`.
2. Fill in a `Capability(...)` (see field reference below, and `specs/001-llm-line-processor/data-model.md` § Capability for the full spec).
3. Save the file. That's it — the registry auto-discovers every module in `capabilities/` at import time (`capabilities/__init__.py`); there is no list to edit.
4. Run `python -m language_capabilities.cli list` — your new capability should appear, labeled, in the tree.
5. Run `python -m language_capabilities.cli run --capability <your-name> --input <a-sample-file>` to try it.

## `Capability` fields

| Field | Required? | Notes |
|---|---|---|
| `name` | yes | Unique slug (e.g. `"german-gloss"`) — this is the value you pass to `--capability`. |
| `description` | yes | One line, shown in `list` output. |
| `language_name` | yes | Human-readable label (e.g. `"German"`), used in progress messages. |
| `system_prompt` | yes | The LLM system prompt. Write it the way the existing `capabilities/*.py` files do — a Python string, triple-quoted or concatenated, describing the persona and the exact JSON shape you want back. |
| `input_format` | yes | One of `"two_line"` (`A:`/`B:` pairs), `"three_line"` (`A:`/`P:`/`B:` triplets — e.g. for romanized languages), `"csv_rows"` (a delimited table), or `"plain_lines"` (one plain line per entry, no translation pairing — for monolingual capabilities like paraphrasing). Pick whichever matches your source file; no new parsing code is needed for these four. |
| `target_field` | required for `two_line`/`three_line` | The key your prompt uses for the source-language word in its JSON response (e.g. `"german"`). Not used for `csv_rows`/`plain_lines`. |
| `output_columns` | yes | Ordered list of CSV column headers, e.g. `["German", "English meaning"]`. Order matters — it's the literal header row. A column named exactly `"Original"` is special-cased to hold the source input line itself (see `paraphrase_en.py`), rather than being matched against the LLM's JSON keys. |
| `include_passthrough_headers` | no | Defaults to `True` (the gloss shape: English + target-language header rows above each line's word breakdown). Set `False` for a capability that wants exactly one output row per input line instead (e.g. paraphrasing). |
| `model` | no | Defaults to `"gpt-4o"`. Set to a local model tag (e.g. `"llama3.2"`) if the capability is meant to run with `--backend local`. |

## A capability that doesn't fit the 3 input formats

If your new use case genuinely needs a new *input format* (not just a new prompt), that's a change to `formats.py` and `engine.py` — outside what "add one file" can do, and outside this feature's scope. The three formats above cover every capability ported from `create_language_video/` and `create_language_video_2/`.
