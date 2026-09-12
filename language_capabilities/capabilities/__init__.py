"""
language_capabilities/capabilities/__init__.py

Capability registry (spec data-model.md § Capability Catalog): auto-discovers
every Capability defined in a module under this package, validates the set,
and exposes it as CATALOG.

Adding a new capability requires no edits here — drop a new module in this
folder that defines a module-level `CAPABILITY = Capability(...)` and it is
picked up automatically the next time the registry loads (see
../NEW_CAPABILITY_GUIDE.md). This is what makes FR-004 possible: registering
a capability is "add one file", not "hand-maintain an import list".
"""

import importlib
import pkgutil
from typing import Dict, List

from ._types import Capability, CapabilityDefinitionError

__all__ = [
    "Capability",
    "CapabilityDefinitionError",
    "DuplicateCapabilityError",
    "register",
    "load_catalog",
    "CATALOG",
]


class DuplicateCapabilityError(ValueError):
    """Raised when two modules register a Capability with the same name
    (spec Edge Cases: "the registry MUST refuse to register the second and
    report the conflict, rather than silently shadowing one")."""


def _discover() -> List[Capability]:
    """Import every non-private module in this package and collect its
    module-level CAPABILITY, if it defines one."""
    found: List[Capability] = []
    for _, module_name, is_pkg in pkgutil.iter_modules(__path__):
        if is_pkg or module_name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{module_name}")
        capability = getattr(module, "CAPABILITY", None)
        if capability is None:
            continue
        if not isinstance(capability, Capability):
            raise CapabilityDefinitionError(
                f"{module_name}.CAPABILITY must be a Capability instance, "
                f"got {type(capability).__name__}"
            )
        found.append(capability)
    return found


def register(capabilities: List[Capability]) -> Dict[str, Capability]:
    """Build a name -> Capability catalog from a list of capabilities,
    refusing (and naming) a duplicate name rather than silently shadowing
    an earlier one. Kept separate from disk discovery so it's directly
    unit-testable (see tests/test_registry.py)."""
    catalog: Dict[str, Capability] = {}
    for capability in capabilities:
        if capability.name in catalog:
            raise DuplicateCapabilityError(
                f"Duplicate capability name {capability.name!r}: already registered "
                f"(a second capability tried to register under the same name)"
            )
        catalog[capability.name] = capability
    return dict(sorted(catalog.items()))


def load_catalog() -> Dict[str, Capability]:
    """Discover + register every capability module found on disk."""
    return register(_discover())


CATALOG: Dict[str, Capability] = load_catalog()
