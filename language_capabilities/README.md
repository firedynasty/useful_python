# language_capabilities

A reusable toolkit that replaces the family of near-duplicated "read a dialogue line, send it to an LLM with a persona prompt, parse the JSON gloss back, write a CSV row" scripts across `create_language_video/` and `create_language_video_2/`. Each existing prompt + input format + output-column bundle is registered here as a **capability** — a small, browsable config file — instead of a whole duplicated script.

The 6 launch capabilities (Mandarin, Cantonese, Filipino, French, Korean, Spanish gloss) were ported verbatim from the original scripts' prompts. Those original scripts are untouched and keep working exactly as before — this toolkit is purely additive.

## Commands

```bash
# Browse every capability: description, input format, output columns.
python -m language_capabilities.cli list

# Run one against an input file (cloud backend, default).
export OPENAI_API_KEY=sk-...
python -m language_capabilities.cli run \
  --capability mandarin-gloss \
  --input create_language_video/dialogue.txt \
  --output output/mandarin_gloss.csv

# Run one against a local LLM instead (e.g. Ollama) — no API key needed.
python -m language_capabilities.cli run \
  --capability paraphrase-en \
  --backend local \
  --input some_lines.txt
```

`--backend local` targets an OpenAI-compatible local server (default `http://localhost:11434/v1/`, Ollama's default — override with `--base-url`), the same pattern already used in `53-webpage_scraper/career-coach.py`.

## Adding a new capability

See [`NEW_CAPABILITY_GUIDE.md`](./NEW_CAPABILITY_GUIDE.md) — it's one new file under `capabilities/`, no engine changes.

## Full documentation

- Spec: `../specs/001-llm-line-processor/spec.md`
- Design: `../specs/001-llm-line-processor/plan.md`, `data-model.md`, `contracts/cli.md`
- Runnable scenarios: `../specs/001-llm-line-processor/quickstart.md`
