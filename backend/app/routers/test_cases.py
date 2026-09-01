from fastapi import APIRouter, HTTPException, Query

from app.prisma_client import db
from app.schemas import TestCaseRead

import asyncio
from datetime import datetime

from fastapi import Response
from app.pdf_generator import build_pdf

router = APIRouter(
    prefix="/test-cases",
    tags=["test-cases"],
)

async def _load_test_cases_for_pdf(
    where_clause: dict,
):
    return await db.test_cases.find_many(
        where=where_clause,
        include={
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
            }
        },
        order={
            "id": "asc"
        }
    )


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


@router.get("", response_model=list[TestCaseRead])
async def list_test_cases(
    category_ids: list[int] | None = Query(default=None),
    test_type_ids: list[int] | None = Query(default=None),
    category_id: int | None = Query(default=None, deprecated=True),
    test_type_id: int | None = Query(default=None, deprecated=True),
):

    effective_category_ids: list[int] = []

    if category_ids:
        effective_category_ids.extend(category_ids)

    if (
        category_id is not None
        and category_id not in effective_category_ids
    ):
        effective_category_ids.append(category_id)

    effective_test_type_ids: list[int] = []

    if test_type_ids:
        effective_test_type_ids.extend(test_type_ids)

    if (
        test_type_id is not None
        and test_type_id not in effective_test_type_ids
    ):
        effective_test_type_ids.append(test_type_id)

    #
    # Handle BOTH wildcard
    #
    if effective_test_type_ids:

        both_row = await db.test_types.find_first(
            where={
                "name": {
                    "equals": "Both"
                }
            }
        )

        if (
            both_row is not None
            and int(both_row.id) in effective_test_type_ids
        ):
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
        include={
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
            }
        },
        order={
            "id": "asc"
        }
    )

    return [
        _map_test_case(tc)
        for tc in test_cases
    ]


@router.get("/{test_case_id}", response_model=TestCaseRead)
async def get_test_case(
    test_case_id: int,
):
    """Get a specific test case by ID."""

    test_case = await db.test_cases.find_unique(
        where={
            "id": test_case_id
        },
        include={
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
            }
        }
    )

    if test_case is None:
        raise HTTPException(
            status_code=404,
            detail="Test case not found",
        )

    return _map_test_case(test_case)


def _map_test_case(tc):

    return {
        "id": int(tc.id),
        "category_id": int(tc.category_id),
        "objective_id": int(tc.objective_id),
        "protocol_id": tc.protocol_id,
        "attack_vector_id": tc.attack_vector_id,
        "test_type_id": tc.test_type_id,
        "severity_id": tc.severity_id,
        "threat_id": tc.threat_id,
        "asset_id": tc.asset_id,
        "action_test_case": tc.action_test_case,
        "source_scope_status": tc.source_scope_status,
        "description": tc.description,
        "attack_path": tc.attack_path,
        "test_steps": tc.test_steps,
        "expected_output": tc.expected_output,
        "attack_feasibility": tc.attack_feasibility,
        "cia_impact": tc.cia_impact,
        "safety_impact": tc.safety_impact,
        "automation_possible": tc.automation_possible,
        "created_at": tc.created_at,

        #
        # Prisma -> Schema mapping
        #
        "category": tc.categories,
        "objective": tc.objectives,
        "protocol": tc.protocols,
        "attack_vector": tc.attack_vectors,
        "test_type": tc.test_types,
        "severity": tc.severities,
        "threat": tc.threats,
        "asset": tc.assets,

        "test_case_tools": [
            {
                "tool": item.tools_master
            }
            for item in tc.test_case_tools
        ],

        "test_case_references": [
            {
                "reference": item.references_master
            }
            for item in tc.test_case_references
        ]
    }

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

    effective_category_ids = []

    if category_ids:
        effective_category_ids.extend(category_ids)

    if (
        category_id is not None
        and category_id not in effective_category_ids
    ):
        effective_category_ids.append(category_id)

    raw_test_type_ids = []

    if test_type_ids:
        raw_test_type_ids.extend(test_type_ids)

    if (
        test_type_id is not None
        and test_type_id not in raw_test_type_ids
    ):
        raw_test_type_ids.append(test_type_id)

    effective_test_type_ids = list(raw_test_type_ids)

    if effective_test_type_ids:

        both_row = await db.test_types.find_first(
            where={
                "name": {
                    "equals": "Both"
                }
            }
        )

        if (
            both_row is not None
            and int(both_row.id) in effective_test_type_ids
        ):
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

    test_cases = await _load_test_cases_for_pdf(
        where_clause
    )

    if not test_cases:
        raise HTTPException(
            status_code=404,
            detail="No test cases found matching the specified filters",
        )

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