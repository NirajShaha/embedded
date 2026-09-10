import asyncio
from datetime import datetime
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
from app.schemas import TestCaseRead


router = APIRouter(
    prefix="/test-cases",
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
    "assets": True,
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
    "",
    response_model=list[TestCaseRead],
)
async def list_test_cases(
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

    return [
        _map_test_case(test_case)
        for test_case in test_cases
    ]


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

    test_cases = await _load_test_cases_for_pdf(
        where_clause
    )

    if not test_cases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No test cases found matching "
                "the specified filters"
            ),
        )

    if test_case_ids is not None:
        returned_test_case_ids = {
            int(test_case.id)
            for test_case in test_cases
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
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return a specific active test case to an authenticated user.
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

    return _map_test_case(test_case)


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
        "asset_id": _optional_int(
            test_case.asset_id
        ),
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
        "automation_possible": (
            test_case.automation_possible
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
        "asset": (
            test_case.assets
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