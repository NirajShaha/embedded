from fastapi import APIRouter, HTTPException, Query

from app.prisma_client import db
from app.schemas import TestCaseOverrideUpdate, TestCaseRead
from app.test_case_overrides import (
    apply_override,
    load_overrides,
    map_test_case,
    map_test_cases,
)

import asyncio
from datetime import datetime

from fastapi import Response
from app.pdf_generator import build_pdf

router = APIRouter(
    prefix="/test-cases",
    tags=["test-cases"],
)

overrides_router = APIRouter(
    prefix="/projects/{project_id}/test-cases",
    tags=["test-cases"],
)

_INCLUDES = {
    "categories": True,
    "objectives": True,
    "protocols": True,
    "attack_vectors": True,
    "test_types": True,
    "severities": True,
    "threats": True,
    "assets": True,
    "test_case_tools": {
        "include": {
            "tools_master": True
        }
    },
    "test_case_references": {
        "include": {
            "references_master": True
        }
    },
}


async def _load_test_cases_for_pdf(
    where_clause: dict,
):
    return await db.test_cases.find_many(
        where=where_clause,
        include=_INCLUDES,
        order={
            "id": "asc"
        }
    )


async def _fetch_test_case(test_case_id: int):
    return await db.test_cases.find_unique(
        where={
            "id": test_case_id
        },
        include=_INCLUDES,
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


@router.get("/categories", response_model=list[dict])
async def get_categories():
    """Get all test categories."""

    categories = await db.categories.find_many(
        order={
            "name": "asc"
        }
    )

    return [
        {
            "id": int(category.id),
            "name": category.name,
        }
        for category in categories
    ]


@router.get("/types", response_model=list[dict])
async def get_test_types():
    """Get all test types."""

    test_types = await db.test_types.find_many(
        order={
            "name": "asc"
        }
    )

    return [
        {
            "id": int(item.id),
            "name": item.name,
        }
        for item in test_types
    ]


@router.get("/tools", response_model=list[dict])
async def list_tools():
    """Get all tools that can be attached to a test case."""

    tools = await db.tools_master.find_many(
        order={
            "tool_name": "asc"
        }
    )

    return [
        {
            "id": int(item.id),
            "tool_name": item.tool_name,
        }
        for item in tools
    ]


@router.get("/references", response_model=list[dict])
async def list_references():
    """Get all reference documents that can be attached to a test case."""

    references = await db.references_master.find_many(
        order={
            "ref_text": "asc"
        }
    )

    return [
        {
            "id": int(item.id),
            "ref_text": item.ref_text,
        }
        for item in references
    ]


def _effective_ids(
    ids: list[int] | None,
    single_id: int | None,
) -> list[int]:
    effective: list[int] = []

    if ids:
        effective.extend(ids)

    if single_id is not None and single_id not in effective:
        effective.append(single_id)

    return effective


async def _is_both_wildcard(effective_test_type_ids: list[int]) -> bool:
    if not effective_test_type_ids:
        return False

    both_row = await db.test_types.find_first(
        where={
            "name": {
                "equals": "Both"
            }
        }
    )

    return both_row is not None and int(both_row.id) in effective_test_type_ids


@router.get("", response_model=list[TestCaseRead])
async def list_test_cases(
    project_id: int | None = Query(default=None),
    category_ids: list[int] | None = Query(default=None),
    test_type_ids: list[int] | None = Query(default=None),
    category_id: int | None = Query(default=None, deprecated=True),
    test_type_id: int | None = Query(default=None, deprecated=True),
):

    effective_category_ids = _effective_ids(category_ids, category_id)
    effective_test_type_ids = _effective_ids(test_type_ids, test_type_id)

    #
    # Handle BOTH wildcard
    #
    if await _is_both_wildcard(effective_test_type_ids):
        effective_test_type_ids = []

    where_clause = {}

    if effective_category_ids:
        where_clause["category_id"] = {
            "in": effective_category_ids
        }

    if effective_test_type_ids:
        where_clause["test_type_id"] = {
            "in": effective_test_type_ids
        }

    test_cases = await db.test_cases.find_many(
        where=where_clause,
        include=_INCLUDES,
        order={
            "id": "asc"
        }
    )

    return await map_test_cases(project_id, test_cases)


@router.get("/export/pdf")
async def export_test_cases_to_pdf(
    project_id: int = Query(...),
    category_ids: list[int] | None = Query(default=None),
    test_type_ids: list[int] | None = Query(default=None),
    category_id: int | None = Query(default=None, deprecated=True),
    test_type_id: int | None = Query(default=None, deprecated=True),
) -> Response:

    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    ecu_detail = await db.project_ecu_details.find_first(
        where={
            "project_id": project_id
        }
    )

    if ecu_detail is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "ECU details have not been added for this project yet. "
                "Please add ECU details before generating the test plan PDF."
            ),
        )

    effective_category_ids = _effective_ids(category_ids, category_id)
    raw_test_type_ids = _effective_ids(test_type_ids, test_type_id)

    effective_test_type_ids = list(raw_test_type_ids)

    if await _is_both_wildcard(effective_test_type_ids):
        effective_test_type_ids = []

    where_clause = {}

    if effective_category_ids:
        where_clause["category_id"] = {
            "in": effective_category_ids
        }

    if effective_test_type_ids:
        where_clause["test_type_id"] = {
            "in": effective_test_type_ids
        }

    rows = await _load_test_cases_for_pdf(
        where_clause
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No test cases found matching the specified filters",
        )

    #
    # Merge each project's overrides over the master catalogue.
    #
    test_cases = await map_test_cases(project_id, rows)

    category_names = []

    if effective_category_ids:

        categories = await db.categories.find_many(
            where={
                "id": {
                    "in": effective_category_ids
                }
            }
        )

        category_names = [
            item.name
            for item in categories
        ]

    test_type_names = []

    if raw_test_type_ids:

        test_types = await db.test_types.find_many(
            where={
                "id": {
                    "in": raw_test_type_ids
                }
            }
        )

        test_type_names = [
            item.name
            for item in test_types
        ]

    pdf_bytes = await asyncio.to_thread(
        build_pdf,
        test_cases,
        ecu_detail,
        category_names if category_names else None,
        test_type_names if test_type_names else None,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = f"test_plan_{timestamp}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        },
    )


@router.get("/{test_case_id}", response_model=TestCaseRead)
async def get_test_case(
    test_case_id: int,
    project_id: int | None = Query(default=None),
):
    """Get a specific test case by ID, with project overrides merged when given."""

    test_case = await _fetch_test_case(test_case_id)

    if test_case is None:
        raise HTTPException(
            status_code=404,
            detail="Test case not found",
        )

    return await _merged_test_case(project_id, test_case)


async def _ensure_project(project_id: int) -> None:
    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )

    if project is None:
        raise HTTPException(
            status_code=404,
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
                "in": unique_ids
            }
        }
    )

    found = {
        int(getattr(row, id_field))
        for row in rows
    }

    if set(unique_ids) != found:
        raise HTTPException(
            status_code=400,
            detail=f"One or more {label} do not exist",
        )


@overrides_router.put("/{test_case_id}", response_model=TestCaseRead)
async def update_test_case_override(
    project_id: int,
    test_case_id: int,
    payload: TestCaseOverrideUpdate,
):
    """Create or update this project's override for a test case.

    Writes to ``project_test_case_overrides`` only; the master ``test_cases`` row is
    never touched.
    """

    await _ensure_project(project_id)

    test_case = await _fetch_test_case(test_case_id)

    if test_case is None:
        raise HTTPException(
            status_code=404,
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
        "updated_at": datetime.now(),
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


@overrides_router.delete("/{test_case_id}", status_code=204)
async def reset_test_case_override(
    project_id: int,
    test_case_id: int,
):
    """Delete this project's override so the master values apply again."""

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
            status_code=404,
            detail="No override exists for this test case",
        )

    await db.project_test_case_overrides.delete(
        where={
            "id": existing.id
        }
    )
