"""Per-project test case overrides.

Users can edit a test case's text fields plus its tools and references while viewing a
project. Those edits are stored in ``project_test_case_overrides`` (and two child link
tables) keyed by ``(project_id, test_case_id)`` so the master ``test_cases`` catalogue is
never modified.

Merge rule: a non-NULL override column replaces the master value. NULL means "not
overridden"; an empty string means the user explicitly cleared the field. Tool and
reference overrides are full replacement sets, flagged by ``tools_overridden`` /
``references_overridden`` so "remove all" is distinguishable from "not overridden".
"""

from __future__ import annotations

from typing import Any

from app.prisma_client import db


EDITABLE_TEXT_FIELDS: tuple[str, ...] = (
    "test_case_name",
    "pre_condition",
    "impact",
    "action_test_case",
    "source_scope_status",
    "description",
    "attack_path",
    "test_steps",
    "expected_output",
    "attack_feasibility",
    "cia_impact",
    "safety_impact",
)


def map_test_case(tc: Any) -> dict:
    """Flatten a Prisma ``test_cases`` row (with includes) into the API shape."""
    return {
        "id": int(tc.id),
        "category_id": int(tc.category_id),
        "objective_id": int(tc.objective_id),
        "protocol_id": tc.protocol_id,
        "attack_vector_id": tc.attack_vector_id,
        "test_type_id": tc.test_type_id,
        "severity_id": tc.severity_id,
        "threat_id": tc.threat_id,
        "test_case_name": tc.test_case_name,
        "pre_condition": tc.pre_condition,
        "impact": tc.impact,
        "action_test_case": tc.action_test_case,
        "source_scope_status": tc.source_scope_status,
        "description": tc.description,
        "attack_path": tc.attack_path,
        "test_steps": tc.test_steps,
        "expected_output": tc.expected_output,
        "attack_feasibility": tc.attack_feasibility,
        "cia_impact": tc.cia_impact,
        "safety_impact": tc.safety_impact,
        "created_at": tc.created_at,
        "category": tc.categories,
        "objective": tc.objectives,
        "protocol": tc.protocols,
        "attack_vector": tc.attack_vectors,
        "test_type": tc.test_types,
        "severity": tc.severities,
        "threat": tc.threats,
        "test_case_tools": [
            {"tool": item.tools_master} for item in tc.test_case_tools
        ],
        "test_case_references": [
            {"reference": item.references_master} for item in tc.test_case_references
        ],
        "is_overridden": False,
    }


def _override_includes() -> dict:
    return {
        "project_test_case_override_tools": {
            "include": {"tools_master": True}
        },
        "project_test_case_override_references": {
            "include": {"references_master": True}
        },
    }


async def load_overrides(
    project_id: int,
    test_case_ids: list[int],
) -> dict[int, Any]:
    """Fetch the override rows for ``test_case_ids`` in a project, keyed by test case id."""
    if not test_case_ids:
        return {}

    rows = await db.project_test_case_overrides.find_many(
        where={
            "project_id": project_id,
            "test_case_id": {"in": test_case_ids},
        },
        include=_override_includes(),
    )

    return {int(row.test_case_id): row for row in rows}


def apply_override(mapped: dict, override: Any) -> dict:
    """Apply a single override row onto the mapped master test case (in place)."""
    for field in EDITABLE_TEXT_FIELDS:
        value = getattr(override, field)
        if value is not None:
            mapped[field] = value

    if override.tools_overridden:
        mapped["test_case_tools"] = [
            {
                "tool": {
                    "id": int(item.tools_master.id),
                    "tool_name": item.tools_master.tool_name,
                }
            }
            for item in override.project_test_case_override_tools
        ]

    if override.references_overridden:
        mapped["test_case_references"] = [
            {
                "reference": {
                    "id": int(item.references_master.id),
                    "ref_text": item.references_master.ref_text,
                }
            }
            for item in override.project_test_case_override_references
        ]

    mapped["is_overridden"] = True
    return mapped


async def map_test_cases(project_id: int | None, test_cases: list[Any]) -> list[dict]:
    """Map master rows and merge any project overrides when ``project_id`` is given."""
    mapped = [map_test_case(tc) for tc in test_cases]

    if project_id is None or not mapped:
        return mapped

    overrides = await load_overrides(project_id, [item["id"] for item in mapped])

    if not overrides:
        return mapped

    for item in mapped:
        override = overrides.get(item["id"])
        if override is not None:
            apply_override(item, override)

    return mapped


async def has_override(project_id: int | None, test_case_id: int) -> bool:
    """True when a project has an override row for the given test case."""
    if project_id is None:
        return False

    row = await db.project_test_case_overrides.find_unique(
        where={
            "project_id_test_case_id": {
                "project_id": project_id,
                "test_case_id": test_case_id,
            }
        }
    )
    return row is not None
