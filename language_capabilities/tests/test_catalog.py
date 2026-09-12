"""
test_catalog.py (T015)

Unit tests for the tree -d -L 2 -style catalog renderer.
"""

import os

from language_capabilities import catalog
from language_capabilities.capabilities import CATALOG

LAUNCH_CAPABILITY_NAMES = {
    "mandarin-gloss",
    "cantonese-gloss",
    "filipino-gloss",
    "french-gloss",
    "korean-gloss",
    "spanish-gloss",
}


def _capabilities_dir() -> str:
    import language_capabilities

    return os.path.join(os.path.dirname(language_capabilities.__file__), "capabilities")


def test_tree_is_depth_two_directories_first():
    rendered = catalog.render_tree(CATALOG, _capabilities_dir())
    lines = rendered.splitlines()
    # First line is the root directory label (depth 0), unindented.
    assert lines[0] == "capabilities"
    # Every subsequent line is a file leaf or its labels (depth 1/2),
    # rendered with tree box-drawing connectors/indentation.
    assert all(line.startswith(("├", "│", "└", " ")) for line in lines[1:])


def test_all_six_launch_capabilities_appear_labeled():
    rendered = catalog.render_tree(CATALOG, _capabilities_dir())
    for name in LAUNCH_CAPABILITY_NAMES:
        capability = CATALOG[name]
        assert capability.description in rendered
        assert capability.input_format in rendered
        for column in capability.output_columns:
            assert column in rendered


def test_missing_capabilities_dir_renders_empty_tree_without_raising():
    rendered = catalog.render_tree(CATALOG, "/does/not/exist")
    assert rendered.splitlines() == ["exist"]
