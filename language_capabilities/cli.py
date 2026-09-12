"""
cli.py

Command-line entry point: `list` (catalog overview, FR-010/FR-013) and
`run` (execute a capability, FR-001/FR-006-FR-009) — see
specs/001-llm-line-processor/contracts/cli.md for the full contract.

`run` supports two backends: "openai" (default — the cloud API every
gloss capability was ported from) and "local" (any OpenAI-compatible local
server, e.g. Ollama's `http://localhost:11434/v1/` — the same pattern
already used in 53-webpage_scraper/career-coach.py).

Usage:
    python -m language_capabilities.cli list
    python -m language_capabilities.cli run --capability mandarin-gloss \
        --input create_language_video/dialogue.txt
    python -m language_capabilities.cli run --capability paraphrase-en \
        --backend local --input some_lines.txt
"""

import argparse
import os
import sys

from . import catalog as catalog_module
from . import engine
from .capabilities import CATALOG

DEFAULT_LOCAL_BASE_URL = "http://localhost:11434/v1/"  # Ollama's default


def _capabilities_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "capabilities")


def _cmd_list(args: argparse.Namespace) -> int:
    """FR-010: list every registered capability without calling the LLM or
    writing any file."""
    print(catalog_module.render_tree(CATALOG, _capabilities_dir()))
    return 0


def _build_client(args: argparse.Namespace):
    """Build the LLM client per --backend. Imported lazily (only inside
    `run`) so `list` never requires the `openai` package to be importable."""
    from openai import OpenAI

    if args.backend == "local":
        # Ollama (and other OpenAI-compatible local servers) don't check
        # the API key, so no real key/precondition is needed here.
        base_url = args.base_url or DEFAULT_LOCAL_BASE_URL
        return OpenAI(api_key="ollama", base_url=base_url)

    # backend == "openai" (default)
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _cmd_run(args: argparse.Namespace) -> int:
    """FR-009: verify preconditions (capability name, input file, and — for
    the "openai" backend only — the API key) before making any API call."""
    capability = CATALOG.get(args.capability)
    if capability is None:
        valid = ", ".join(sorted(CATALOG)) or "(no capabilities registered)"
        print(
            f"Error: unknown capability {args.capability!r}. "
            f"Valid capabilities: {valid}",
            file=sys.stderr,
        )
        return 1

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    if args.backend == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: OPENAI_API_KEY not set. Export it first:\n"
            "  export OPENAI_API_KEY=sk-...\n"
            "(or pass --backend local to use a local server like Ollama instead)",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or os.path.join("output", f"{capability.name}.csv")
    client = _build_client(args)

    engine.run_capability(
        client=client,
        capability=capability,
        input_path=args.input,
        output_path=output_path,
        model=args.model,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="language_capabilities",
        description="Run or browse LLM line-processing capabilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list", help="Print a labeled tree of every registered capability."
    )

    run_parser = subparsers.add_parser(
        "run", help="Run a capability against an input file."
    )
    run_parser.add_argument(
        "--capability", required=True, help="Capability name, e.g. mandarin-gloss"
    )
    run_parser.add_argument(
        "--input", required=True, help="Path to the input document"
    )
    run_parser.add_argument(
        "--output",
        default=None,
        help="Path for output CSV (default: output/<capability>.csv)",
    )
    run_parser.add_argument(
        "--model", default=None, help="Override the capability's default model"
    )
    run_parser.add_argument(
        "--backend",
        choices=["openai", "local"],
        default="openai",
        help=(
            "Which LLM backend to call (default: openai). 'local' targets an "
            "OpenAI-compatible local server (e.g. Ollama) and needs no API key."
        ),
    )
    run_parser.add_argument(
        "--base-url",
        default=None,
        help=(
            "Override the local backend's base URL "
            f"(default: {DEFAULT_LOCAL_BASE_URL}, Ollama's default). "
            "Ignored for --backend openai."
        ),
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "run":
        return _cmd_run(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
