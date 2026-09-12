"""
test_registry.py (T012)

Unit tests for the capability registry (language_capabilities/capabilities/).
"""

import pytest

from language_capabilities.capabilities import CATALOG, DuplicateCapabilityError, register
from language_capabilities.capabilities._types import Capability, CapabilityDefinitionError

LAUNCH_CAPABILITY_NAMES = {
    "mandarin-gloss",
    "cantonese-gloss",
    "filipino-gloss",
    "french-gloss",
    "korean-gloss",
    "spanish-gloss",
}


def test_all_six_launch_capabilities_are_registered():
    assert LAUNCH_CAPABILITY_NAMES.issubset(CATALOG.keys())


def _make_capability(name: str) -> Capability:
    return Capability(
        name=name,
        description="test capability",
        language_name="Testlandish",
        system_prompt="a valid, non-empty prompt",
        input_format="two_line",
        target_field="test",
        output_columns=["Test", "English meaning"],
    )


def test_duplicate_name_is_refused_and_names_the_conflict():
    first = _make_capability("dup-test")
    second = _make_capability("dup-test")
    with pytest.raises(DuplicateCapabilityError, match="dup-test"):
        register([first, second])


def test_non_duplicate_names_register_together():
    catalog = register([_make_capability("a-test"), _make_capability("b-test")])
    assert set(catalog) == {"a-test", "b-test"}


def test_two_line_capability_without_target_field_fails_validation():
    with pytest.raises(CapabilityDefinitionError, match="target_field"):
        Capability(
            name="broken",
            description="d",
            language_name="X",
            system_prompt="p",
            input_format="two_line",
            target_field="",
            output_columns=["X", "English meaning"],
        )


def test_csv_rows_capability_does_not_require_target_field():
    # Should not raise: target_field is optional for csv_rows.
    capability = Capability(
        name="csv-test",
        description="d",
        language_name="X",
        system_prompt="p",
        input_format="csv_rows",
        target_field="",
        output_columns=["X", "English meaning"],
    )
    assert capability.target_field == ""


def test_empty_output_columns_fails_validation():
    with pytest.raises(CapabilityDefinitionError, match="output_columns"):
        Capability(
            name="broken2",
            description="d",
            language_name="X",
            system_prompt="p",
            input_format="two_line",
            target_field="x",
            output_columns=[],
        )
