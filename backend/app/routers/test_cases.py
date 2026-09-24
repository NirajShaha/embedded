import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from app.auth import get_current_user
from app.pdf_generator import build_pdf
from app.prisma_client import db
from app.schemas import CreateLookupItemPayload, TestCaseOverrideUpdate, TestCaseRead
from app.test_case_overrides import (
    apply_override,
    load_overrides,
    map_test_case,
    map_test_cases,
)


router = APIRouter(
    prefix="/test-cases",
    tags=["test-cases"],
)


@router.post("/lookups/{lookup_type}")
async def create_user_lookup_item(
    lookup_type: str,
    payload: CreateLookupItemPayload,
    _current_user=Depends(get_current_user),
):
    """Create a reusable tool/reference for a project override selection."""
    name = payload.name.strip()
    if not name or lookup_type not in {"tools", "references"}:
        raise HTTPException(status_code=400, detail="Only tools and references can be added here")

    if lookup_type == "tools":
        existing = await db.tools_master.find_first(where={"tool_name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.tool_name}
        item = await db.tools_master.create(data={"tool_name": name})
        return {"id": int(item.id), "name": item.tool_name}

    existing = await db.references_master.find_first(where={"ref_text": name})
    if existing:
        return {"id": int(existing.id), "name": existing.ref_text}
    item = await db.references_master.create(data={"ref_text": name})
    return {"id": int(item.id), "name": item.ref_text}

overrides_router = APIRouter(
    prefix="/projects/{project_id}/test-cases",
    tags=["test-cases"],
)

TEST_CASE_INCLUDE = {
    "categories": True,
    "objectives": True,
    "protocols": True,
    "attack_vectors": True,
    "test_types": True,
    "severities": True,
    "threats": True,
    "test_case_tools": {
        "include": {
            "tools_master": True,
        }
    },
    "test_case_references": {
        "include": {
            "references_master": True,
        }
    },
}


async def _load_test_cases_for_pdf(
    where_clause: dict[str, Any],
):
    """
    Load test cases and all relationships required
    for PDF generation.
    """

    return await db.test_cases.find_many(
        where=where_clause,
        include=TEST_CASE_INCLUDE,
        order={
            "id": "asc",
        },
    )


async def _resolve_test_type_filters(
    test_type_ids: list[int] | None,
    legacy_test_type_id: int | None,
) -> tuple[list[int], list[int]]:
    """
    Resolve raw and effective test-type filters.

    raw_test_type_ids:
        Original normalized IDs used for PDF metadata.

    effective_test_type_ids:
        IDs actually used to filter test cases.

    If the test type named 'Both' is selected, the effective
    filter is cleared so test cases from all test types are returned.
    """

    raw_test_type_ids = sorted(
        {
            current_test_type_id
            for current_test_type_id in (
                test_type_ids or []
            )
            if current_test_type_id > 0
        }
    )

    if (
        legacy_test_type_id is not None
        and legacy_test_type_id > 0
        and legacy_test_type_id
        not in raw_test_type_ids
    ):
        raw_test_type_ids.append(
            legacy_test_type_id
        )

    raw_test_type_ids.sort()

    effective_test_type_ids = list(
        raw_test_type_ids
    )

    if effective_test_type_ids:
        both_row = (
            await db.test_types.find_first(
                where={
                    "name": {
                        "equals": "Both",
                    }
                }
            )
        )

        if (
            both_row is not None
            and int(both_row.id)
            in effective_test_type_ids
        ):
            effective_test_type_ids = []

    return (
        raw_test_type_ids,
        effective_test_type_ids,
    )


def _resolve_category_filters(
    category_ids: list[int] | None,
    legacy_category_id: int | None,
) -> list[int]:
    """
    Normalize, deduplicate, and sort category filter IDs.
    """

    effective_category_ids = sorted(
        {
            current_category_id
            for current_category_id in (
                category_ids or []
            )
            if current_category_id > 0
        }
    )

    if (
        legacy_category_id is not None
        and legacy_category_id > 0
        and legacy_category_id
        not in effective_category_ids
    ):
        effective_category_ids.append(
            legacy_category_id
        )

    effective_category_ids.sort()

    return effective_category_ids


def _normalize_test_case_ids(
    test_case_ids: list[int] | None,
) -> list[int]:
    """
    Normalize, deduplicate, and sort selected test-case IDs.
    """

    return sorted(
        {
            test_case_id
            for test_case_id in (
                test_case_ids or []
            )
            if test_case_id > 0
        }
    )


async def _merged_test_case(project_id: int | None, test_case) -> dict:
    """Map one test case and merge the project's override, if any."""
    mapped = map_test_case(test_case)

    if project_id is None:
        return mapped

    overrides = await load_overrides(project_id, [mapped["id"]])
    override = overrides.get(mapped["id"])

    if override is not None:
        apply_override(mapped, override)

    return mapped


@router.get(
    "/categories",
    response_model=list[dict],
)
async def get_categories(
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return all test categories to an authenticated user.
    """

    categories = await db.categories.find_many(
        order={
            "name": "asc",
        }
    )

    return [
        {
            "id": int(category.id),
            "name": category.name,
        }
        for category in categories
    ]


@router.get(
    "/types",
    response_model=list[dict],
)
async def get_test_types(
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return all test types to an authenticated user.
    """

    test_types = await db.test_types.find_many(
        order={
            "name": "asc",
        }
    )

    return [
        {
            "id": int(test_type.id),
            "name": test_type.name,
        }
        for test_type in test_types
    ]


@router.get(
    "/classification-lookups",
    response_model=dict[str, list[dict]],
)
async def get_classification_lookups(
    _current_user=Depends(get_current_user),
):
    return {
        "categories": [
            {"id": int(item.id), "name": item.name}
            for item in await db.categories.find_many(order={"name": "asc"})
        ],
        "objectives": [
            {
                "id": int(item.id),
                "name": item.name,
                "category_id": int(item.category_id),
            }
            for item in await db.objectives.find_many(order={"name": "asc"})
        ],
        "protocols": [
            {"id": int(item.id), "name": item.name}
            for item in await db.protocols.find_many(order={"name": "asc"})
        ],
        "attack_vectors": [
            {"id": int(item.id), "name": item.name}
            for item in await db.attack_vectors.find_many(order={"name": "asc"})
        ],
        "test_types": [
            {"id": int(item.id), "name": item.name}
            for item in await db.test_types.find_many(order={"name": "asc"})
        ],
        "severities": [
            {"id": int(item.id), "name": item.name}
            for item in await db.severities.find_many(order={"severity_rank": "asc"})
        ],
        "threats": [
            {"id": int(item.id), "name": item.threat_text}
            for item in await db.threats.find_many(order={"id": "asc"})
        ],
    }


@router.get(
    "/tools",
    response_model=list[dict],
)
async def list_tools(
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return all tools that can be attached to a test case.
    """

    tools = await db.tools_master.find_many(
        order={
            "tool_name": "asc",
        }
    )

    return [
        {
            "id": int(item.id),
            "tool_name": item.tool_name,
        }
        for item in tools
    ]


@router.get(
    "/references",
    response_model=list[dict],
)
async def list_references(
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return all reference documents that can be attached to a test case.
    """

    references = await db.references_master.find_many(
        order={
            "ref_text": "asc",
        }
    )

    return [
        {
            "id": int(item.id),
            "ref_text": item.ref_text,
        }
        for item in references
    ]


@router.get(
    "",
    response_model=list[TestCaseRead],
)
async def list_test_cases(
    project_id: int | None = Query(
        default=None,
    ),
    category_ids: list[int] | None = Query(
        default=None,
    ),
    test_type_ids: list[int] | None = Query(
        default=None,
    ),
    category_id: int | None = Query(
        default=None,
        deprecated=True,
    ),
    test_type_id: int | None = Query(
        default=None,
        deprecated=True,
    ),
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return active test cases matching the supplied filters.
    """

    effective_category_ids = (
        _resolve_category_filters(
            category_ids,
            category_id,
        )
    )

    (
        _raw_test_type_ids,
        effective_test_type_ids,
    ) = await _resolve_test_type_filters(
        test_type_ids,
        test_type_id,
    )

    where_clause: dict[str, Any] = {
        "deleted_at": None,
    }

    if effective_category_ids:
        where_clause["category_id"] = {
            "in": effective_category_ids,
        }

    if effective_test_type_ids:
        where_clause["test_type_id"] = {
            "in": effective_test_type_ids,
        }

    test_cases = await db.test_cases.find_many(
        where=where_clause,
        include=TEST_CASE_INCLUDE,
        order={
            "id": "asc",
        },
    )

    return await map_test_cases(project_id, test_cases)


@router.get("/export/pdf")
async def export_test_cases_to_pdf(
    project_id: int = Query(
        ...,
        gt=0,
    ),
    test_case_ids: list[int] | None = Query(
        default=None,
    ),
    category_ids: list[int] | None = Query(
        default=None,
    ),
    test_type_ids: list[int] | None = Query(
        default=None,
    ),
    category_id: int | None = Query(
        default=None,
        deprecated=True,
    ),
    test_type_id: int | None = Query(
        default=None,
        deprecated=True,
    ),
    _current_user=Depends(
        get_current_user
    ),
) -> Response:
    """
    Generate a PDF for an authenticated user's project
    and selected active test cases.
    """

    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    ecu_detail = (
        await db.project_ecu_details.find_first(
            where={
                "project_id": project_id,
            }
        )
    )

    if ecu_detail is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "ECU details have not been added "
                "for this project yet. Please add "
                "ECU details before generating the "
                "test plan PDF."
            ),
        )

    effective_category_ids = (
        _resolve_category_filters(
            category_ids,
            category_id,
        )
    )

    (
        raw_test_type_ids,
        effective_test_type_ids,
    ) = await _resolve_test_type_filters(
        test_type_ids,
        test_type_id,
    )

    effective_test_case_ids = (
        _normalize_test_case_ids(
            test_case_ids
        )
    )

    if (
        test_case_ids is not None
        and not effective_test_case_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No test cases were selected "
                "for PDF generation"
            ),
        )

    where_clause: dict[str, Any] = {
        "deleted_at": None,
    }

    if test_case_ids is not None:
        where_clause["id"] = {
            "in": effective_test_case_ids,
        }

    if effective_category_ids:
        where_clause["category_id"] = {
            "in": effective_category_ids,
        }

    if effective_test_type_ids:
        where_clause["test_type_id"] = {
            "in": effective_test_type_ids,
        }

    rows = await _load_test_cases_for_pdf(
        where_clause
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No test cases found matching "
                "the specified filters"
            ),
        )

    if test_case_ids is not None:
        returned_test_case_ids = {
            int(row.id)
            for row in rows
        }

        requested_test_case_ids = set(
            effective_test_case_ids
        )

        unavailable_test_case_ids = sorted(
            requested_test_case_ids
            - returned_test_case_ids
        )

        if unavailable_test_case_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "One or more selected test cases "
                    "are no longer available or no "
                    "longer match the selected filters. "
                    "Refresh the dashboard and try again."
                ),
            )

    #
    # Merge each project's overrides over the master catalogue.
    #
    test_cases = await map_test_cases(project_id, rows)

    category_names: list[str] = []

    if effective_category_ids:
        categories = (
            await db.categories.find_many(
                where={
                    "id": {
                        "in": (
                            effective_category_ids
                        ),
                    }
                },
                order={
                    "name": "asc",
                },
            )
        )

        category_names = [
            category.name
            for category in categories
        ]

    test_type_names: list[str] = []

    if raw_test_type_ids:
        test_types = (
            await db.test_types.find_many(
                where={
                    "id": {
                        "in": (
                            raw_test_type_ids
                        ),
                    }
                },
                order={
                    "name": "asc",
                },
            )
        )

        test_type_names = [
            test_type.name
            for test_type in test_types
        ]

    pdf_bytes = await asyncio.to_thread(
        build_pdf,
        test_cases,
        ecu_detail,
        (
            category_names
            if category_names
            else None
        ),
        (
            test_type_names
            if test_type_names
            else None
        ),
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"test_plan_{timestamp}.pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                "attachment; "
                f'filename="{filename}"'
            )
        },
    )


@router.get(
    "/{test_case_id}",
    response_model=TestCaseRead,
)
async def get_test_case(
    test_case_id: int,
    project_id: int | None = Query(
        default=None,
    ),
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return a specific active test case, with project overrides merged when given.
    """

    test_case = await db.test_cases.find_first(
        where={
            "id": test_case_id,
            "deleted_at": None,
        },
        include=TEST_CASE_INCLUDE,
    )

    if test_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found",
        )

    return await _merged_test_case(project_id, test_case)


def _optional_int(
    value,
) -> int | None:
    """
    Convert an optional Prisma BigInt value into a JSON-safe int.
    """

    if value is None:
        return None

    return int(value)


def _map_test_case(
    test_case,
) -> dict[str, Any]:
    """
    Map a Prisma test-case record to the API response structure.

    Kept for the admin router import; dashboard reads use the
    override-aware mapper in app.test_case_overrides.
    """

    return {
        "id": int(
            test_case.id
        ),
        "category_id": int(
            test_case.category_id
        ),
        "objective_id": int(
            test_case.objective_id
        ),
        "protocol_id": _optional_int(
            test_case.protocol_id
        ),
        "attack_vector_id": _optional_int(
            test_case.attack_vector_id
        ),
        "test_type_id": _optional_int(
            test_case.test_type_id
        ),
        "severity_id": _optional_int(
            test_case.severity_id
        ),
        "threat_id": _optional_int(
            test_case.threat_id
        ),
        "test_case_name": test_case.test_case_name,
        "pre_condition": test_case.pre_condition,
        "impact": test_case.impact,
        "action_test_case": (
            test_case.action_test_case
        ),
        "source_scope_status": (
            test_case.source_scope_status
        ),
        "description": (
            test_case.description
        ),
        "attack_path": (
            test_case.attack_path
        ),
        "test_steps": (
            test_case.test_steps
        ),
        "expected_output": (
            test_case.expected_output
        ),
        "attack_feasibility": (
            test_case.attack_feasibility
        ),
        "cia_impact": (
            test_case.cia_impact
        ),
        "safety_impact": (
            test_case.safety_impact
        ),
        "created_at": (
            test_case.created_at
        ),
        "category": (
            test_case.categories
        ),
        "objective": (
            test_case.objectives
        ),
        "protocol": (
            test_case.protocols
        ),
        "attack_vector": (
            test_case.attack_vectors
        ),
        "test_type": (
            test_case.test_types
        ),
        "severity": (
            test_case.severities
        ),
        "threat": (
            test_case.threats
        ),
        "test_case_tools": [
            {
                "tool": (
                    item.tools_master
                ),
            }
            for item in (
                test_case.test_case_tools
            )
        ],
        "test_case_references": [
            {
                "reference": (
                    item.references_master
                ),
            }
            for item in (
                test_case.test_case_references
            )
        ],
    }


async def _ensure_project(project_id: int) -> None:
    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )


async def _ensure_ids_exist(
    model,
    id_field: str,
    ids: list[int],
    label: str,
) -> None:
    if not ids:
        return

    unique_ids = sorted(set(ids))

    rows = await model.find_many(
        where={
            "id": {
                "in": unique_ids,
            }
        }
    )

    found = {
        int(getattr(row, id_field))
        for row in rows
    }

    if set(unique_ids) != found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"One or more {label} do not exist",
        )


@overrides_router.put(
    "/{test_case_id}",
    response_model=TestCaseRead,
)
async def update_test_case_override(
    project_id: int,
    test_case_id: int,
    payload: TestCaseOverrideUpdate,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Create or update this project's override for a test case.

    Writes to ``project_test_case_overrides`` only; the master
    ``test_cases`` row is never touched.
    """

    await _ensure_project(project_id)

    test_case = await db.test_cases.find_first(
        where={
            "id": test_case_id,
            "deleted_at": None,
        },
        include=TEST_CASE_INCLUDE,
    )

    if test_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found",
        )

    if payload.tools is not None:
        await _ensure_ids_exist(
            db.tools_master,
            "id",
            payload.tools,
            "tools",
        )

    if payload.references is not None:
        await _ensure_ids_exist(
            db.references_master,
            "id",
            payload.references,
            "references",
        )

    text_data = payload.model_dump(exclude={"tools", "references"})

    create_data = {
        "project_id": project_id,
        "test_case_id": test_case_id,
        **text_data,
        "tools_overridden": payload.tools is not None,
        "references_overridden": payload.references is not None,
    }

    update_data = {
        **text_data,
        "updated_at": datetime.now(timezone.utc),
    }

    if payload.tools is not None:
        update_data["tools_overridden"] = True

    if payload.references is not None:
        update_data["references_overridden"] = True

    override = await db.project_test_case_overrides.upsert(
        where={
            "project_id_test_case_id": {
                "project_id": project_id,
                "test_case_id": test_case_id,
            }
        },
        data={
            "create": create_data,
            "update": update_data,
        },
    )

    if payload.tools is not None:

        await db.project_test_case_override_tools.delete_many(
            where={
                "override_id": override.id
            }
        )

        for tool_id in sorted(set(payload.tools)):
            await db.project_test_case_override_tools.create(
                data={
                    "override_id": override.id,
                    "tool_id": tool_id,
                }
            )

    if payload.references is not None:

        await db.project_test_case_override_references.delete_many(
            where={
                "override_id": override.id
            }
        )

        for reference_id in sorted(set(payload.references)):
            await db.project_test_case_override_references.create(
                data={
                    "override_id": override.id,
                    "reference_id": reference_id,
                }
            )

    #
    # A row that overrides nothing is noise; drop it so the UI doesn't claim
    # the test case was edited.
    #
    has_text = any(value is not None for value in text_data.values())

    if (
        not has_text
        and not override.tools_overridden
        and not override.references_overridden
    ):
        await db.project_test_case_overrides.delete(
            where={
                "id": override.id
            }
        )

        return map_test_case(test_case)

    return await _merged_test_case(project_id, test_case)


@overrides_router.delete(
    "/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_test_case_override(
    project_id: int,
    test_case_id: int,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Delete this project's override so the master values apply again.
    """

    await _ensure_project(project_id)

    existing = await db.project_test_case_overrides.find_unique(
        where={
            "project_id_test_case_id": {
                "project_id": project_id,
                "test_case_id": test_case_id,
            }
        }
    )

    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No override exists for this test case",
        )

    await db.project_test_case_overrides.delete(
        where={
            "id": existing.id
        }
    )
