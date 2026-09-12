"""
catalog.py

Renders the Capability Catalog as a `tree -d -L 2`-style, labeled overview
(FR-013): a pure-Python renderer (no subprocess call to the system `tree`
binary — see specs/001-llm-line-processor/research.md § 4) that walks
language_capabilities/capabilities/ to depth 2 (the root directory, then its
files — the package has no deeper subfolders today), directories before
files, printing each capability's file as a labeled leaf.
"""

import os
from typing import Dict, Optional

from .capabilities import Capability


def _capability_for_filename(catalog: Dict[str, Capability], filename: str) -> Optional[Capability]:
    """Match a capabilities/ module filename (e.g. "mandarin_gloss.py") back
    to its registered Capability by comparing the module stem to the
    capability's name with hyphens turned into underscores."""
    module_stem = filename[:-3] if filename.endswith(".py") else filename
    for capability in catalog.values():
        if capability.name.replace("-", "_") == module_stem:
            return capability
    return None


def render_tree(catalog: Dict[str, Capability], capabilities_dir: str) -> str:
    """Render a `tree -d -L 2`-shaped, labeled view of `capabilities_dir`.

    `catalog`: dict[name -> Capability] (typically capabilities.CATALOG).
    `capabilities_dir`: filesystem path to the capabilities/ package.

    Returns the rendered tree as a single string (no trailing newline).
    """
    root_label = os.path.basename(os.path.normpath(capabilities_dir))
    lines = [root_label]

    try:
        entries = sorted(
            entry
            for entry in os.listdir(capabilities_dir)
            if entry.endswith(".py") and not entry.startswith("_")
        )
    except FileNotFoundError:
        entries = []

    for index, filename in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "
        continuation = "    " if is_last else "│   "
        lines.append(f"{connector}{filename}")

        capability = _capability_for_filename(catalog, filename)
        if capability is None:
            lines.append(f"{continuation}(not registered — see ../NEW_CAPABILITY_GUIDE.md)")
            continue

        lines.append(f"{continuation}{capability.description}")
        lines.append(
            f"{continuation}input: {capability.input_format}"
            f"  columns: {', '.join(capability.output_columns)}"
        )

    return "\n".join(lines)
