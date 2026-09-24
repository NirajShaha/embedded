from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth import require_admin
from app.prisma_client import db
from app.schemas import (
    AdminStatsRead,
    CreateLookupItemPayload,
    FieldSuggestions,
    LookupItem,
    TestCaseCreate,
    TestCaseLookups,
    TestCaseRead,
    TestCaseUpdate,
)
from app.routers.test_cases import _map_test_case


router = APIRouter(
    prefix="/admin",
    tags=["administration"],
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


def _clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


async def _ensure_record_exists(
    *,
    client,
    record_id: int | None,
    label: str,
) -> None:
    if record_id is None:
        return

    record = await client.find_unique(
        where={
            "id": record_id,
        }
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{label} does not exist",
        )


async def _validate_relations(
    *,
    category_id: int,
    objective_id: int,
    protocol_id: int | None,
    attack_vector_id: int | None,
    test_type_id: int | None,
    severity_id: int | None,
    threat_id: int | None,
    tool_ids: list[int],
    reference_ids: list[int],
) -> None:
    category = await db.categories.find_unique(
        where={
            "id": category_id,
        }
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category does not exist",
        )

    objective = await db.objectives.find_unique(
        where={
            "id": objective_id,
        }
    )

    if objective is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Objective does not exist",
        )

    if int(objective.category_id) != category_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Selected objective does not belong "
                "to the selected category"
            ),
        )

    await _ensure_record_exists(
        client=db.protocols,
        record_id=protocol_id,
        label="Protocol",
    )

    await _ensure_record_exists(
        client=db.attack_vectors,
        record_id=attack_vector_id,
        label="Attack vector",
    )

    await _ensure_record_exists(
        client=db.test_types,
        record_id=test_type_id,
        label="Test type",
    )

    await _ensure_record_exists(
        client=db.severities,
        record_id=severity_id,
        label="Severity",
    )

    await _ensure_record_exists(
        client=db.threats,
        record_id=threat_id,
        label="Threat",
    )

    unique_tool_ids = sorted(
        set(tool_ids)
    )

    if unique_tool_ids:
        tools = await db.tools_master.find_many(
            where={
                "id": {
                    "in": unique_tool_ids,
                }
            }
        )

        found_ids = {
            int(tool.id)
            for tool in tools
        }

        if found_ids != set(unique_tool_ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="One or more selected tools do not exist",
            )

    unique_reference_ids = sorted(
        set(reference_ids)
    )

    if unique_reference_ids:
        references = await db.references_master.find_many(
            where={
                "id": {
                    "in": unique_reference_ids,
                }
            }
        )

        found_ids = {
            int(reference.id)
            for reference in references
        }

        if found_ids != set(unique_reference_ids):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "One or more selected references "
                    "do not exist"
                ),
            )


async def _get_active_test_case(
    test_case_id: int,
):
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

    return test_case


async def _ensure_not_duplicate(
    *,
    objective_id: int,
    action_test_case: str,
    excluding_test_case_id: int | None = None,
) -> None:
    conditions: dict = {
        "objective_id": objective_id,
        "action_test_case": action_test_case,
        "deleted_at": None,
    }

    if excluding_test_case_id is not None:
        conditions["id"] = {
            "not": excluding_test_case_id,
        }

    duplicate = await db.test_cases.find_first(
        where=conditions
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A test case with this objective and "
                "action already exists"
            ),
        )


@router.get(
    "/lookups",
    response_model=TestCaseLookups,
)
async def get_test_case_lookups(
    _current_admin=Depends(require_admin),
):
    categories = await db.categories.find_many(
        order={
            "name": "asc",
        }
    )

    objectives = await db.objectives.find_many(
        order={
            "id": "asc",
        }
    )

    protocols = await db.protocols.find_many(
        order={
            "name": "asc",
        }
    )

    attack_vectors = await db.attack_vectors.find_many(
        order={
            "name": "asc",
        }
    )

    test_types = await db.test_types.find_many(
        order={
            "name": "asc",
        }
    )

    severities = await db.severities.find_many(
        order={
            "severity_rank": "asc",
        }
    )

    threats = await db.threats.find_many(
        order={
            "id": "asc",
        }
    )

    tools = await db.tools_master.find_many(
        order={
            "tool_name": "asc",
        }
    )

    references = await db.references_master.find_many(
        order={
            "id": "asc",
        }
    )

    return {
        "categories": [
            {
                "id": int(item.id),
                "name": item.name,
            }
            for item in categories
        ],
        "objectives": [
            {
                "id": int(item.id),
                "name": item.name,
                "category_id": int(item.category_id),
            }
            for item in objectives
        ],
        "protocols": [
            {
                "id": int(item.id),
                "name": item.name,
            }
            for item in protocols
        ],
        "attack_vectors": [
            {
                "id": int(item.id),
                "name": item.name,
            }
            for item in attack_vectors
        ],
        "test_types": [
            {
                "id": int(item.id),
                "name": item.name,
            }
            for item in test_types
        ],
        "severities": [
            {
                "id": int(item.id),
                "name": item.name,
                "severity_rank": item.severity_rank,
            }
            for item in severities
        ],
        "threats": [
            {
                "id": int(item.id),
                "name": item.threat_text,
            }
            for item in threats
        ],
        "tools": [
            {
                "id": int(item.id),
                "name": item.tool_name,
            }
            for item in tools
        ],
        "references": [
            {
                "id": int(item.id),
                "name": item.ref_text,
            }
            for item in references
        ],
    }


@router.get(
    "/test-cases",
    response_model=list[TestCaseRead],
)
async def list_admin_test_cases(
    _current_admin=Depends(require_admin),
):
    test_cases = await db.test_cases.find_many(
        where={
            "deleted_at": None,
        },
        include=TEST_CASE_INCLUDE,
        order={
            "id": "desc",
        },
    )

    return [
        _map_test_case(test_case)
        for test_case in test_cases
    ]


@router.get(
    "/test-cases/{test_case_id}",
    response_model=TestCaseRead,
)
async def get_admin_test_case(
    test_case_id: int,
    _current_admin=Depends(require_admin),
):
    test_case = await _get_active_test_case(
        test_case_id
    )

    return _map_test_case(test_case)


@router.post(
    "/test-cases",
    response_model=TestCaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_test_case(
    payload: TestCaseCreate,
    current_admin=Depends(require_admin),
):
    action_test_case = payload.action_test_case.strip()

    if not action_test_case:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Action/Test Case is required",
        )

    tool_ids = sorted(
        set(payload.tool_ids)
    )

    reference_ids = sorted(
        set(payload.reference_ids)
    )

    await _validate_relations(
        category_id=payload.category_id,
        objective_id=payload.objective_id,
        protocol_id=payload.protocol_id,
        attack_vector_id=payload.attack_vector_id,
        test_type_id=payload.test_type_id,
        severity_id=payload.severity_id,
        threat_id=payload.threat_id,
        tool_ids=tool_ids,
        reference_ids=reference_ids,
    )

    await _ensure_not_duplicate(
        objective_id=payload.objective_id,
        action_test_case=action_test_case,
    )

    async with db.tx() as transaction:
        created = await transaction.test_cases.create(
            data={
                "category_id": payload.category_id,
                "objective_id": payload.objective_id,
                "protocol_id": payload.protocol_id,
                "attack_vector_id": payload.attack_vector_id,
                "test_type_id": payload.test_type_id,
                "severity_id": payload.severity_id,
                "threat_id": payload.threat_id,
                "test_case_name": _clean_optional_text(
                    payload.test_case_name
                ),
                "pre_condition": _clean_optional_text(
                    payload.pre_condition
                ),
                "impact": _clean_optional_text(
                    payload.impact
                ),
                "action_test_case": action_test_case,
                "description": _clean_optional_text(
                    payload.description
                ),
                "attack_path": _clean_optional_text(
                    payload.attack_path
                ),
                "test_steps": _clean_optional_text(
                    payload.test_steps
                ),
                "expected_output": _clean_optional_text(
                    payload.expected_output
                ),
                "attack_feasibility": _clean_optional_text(
                    payload.attack_feasibility
                ),
                "cia_impact": _clean_optional_text(
                    payload.cia_impact
                ),
                "safety_impact": _clean_optional_text(
                    payload.safety_impact
                ),
                "created_by": int(current_admin.id),
                "updated_by": int(current_admin.id),
            }
        )

        for tool_id in tool_ids:
            await transaction.test_case_tools.create(
                data={
                    "test_case_id": created.id,
                    "tool_id": tool_id,
                }
            )

        for reference_id in reference_ids:
            await transaction.test_case_references.create(
                data={
                    "test_case_id": created.id,
                    "reference_id": reference_id,
                }
            )

    saved = await _get_active_test_case(
        int(created.id)
    )

    return _map_test_case(saved)


@router.put(
    "/test-cases/{test_case_id}",
    response_model=TestCaseRead,
)
async def update_admin_test_case(
    test_case_id: int,
    payload: TestCaseUpdate,
    current_admin=Depends(require_admin),
):
    existing = await _get_active_test_case(
        test_case_id
    )

    supplied = payload.model_dump(
        exclude_unset=True
    )

    category_id = supplied.get(
        "category_id",
        int(existing.category_id),
    )

    objective_id = supplied.get(
        "objective_id",
        int(existing.objective_id),
    )

    action_test_case = supplied.get(
        "action_test_case",
        existing.action_test_case,
    )

    action_test_case = action_test_case.strip()

    if not action_test_case:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Action/Test Case is required",
        )

    if payload.tool_ids is None:
        tool_ids = [
            int(item.tool_id)
            for item in existing.test_case_tools
        ]
    else:
        tool_ids = sorted(
            set(payload.tool_ids)
        )

    if payload.reference_ids is None:
        reference_ids = [
            int(item.reference_id)
            for item in existing.test_case_references
        ]
    else:
        reference_ids = sorted(
            set(payload.reference_ids)
        )

    final_protocol_id = (
        supplied["protocol_id"]
        if "protocol_id" in supplied
        else existing.protocol_id
    )

    final_attack_vector_id = (
        supplied["attack_vector_id"]
        if "attack_vector_id" in supplied
        else existing.attack_vector_id
    )

    final_test_type_id = (
        supplied["test_type_id"]
        if "test_type_id" in supplied
        else existing.test_type_id
    )

    final_severity_id = (
        supplied["severity_id"]
        if "severity_id" in supplied
        else existing.severity_id
    )

    final_threat_id = (
        supplied["threat_id"]
        if "threat_id" in supplied
        else existing.threat_id
    )

    await _validate_relations(
        category_id=category_id,
        objective_id=objective_id,
        protocol_id=final_protocol_id,
        attack_vector_id=final_attack_vector_id,
        test_type_id=final_test_type_id,
        severity_id=final_severity_id,
        threat_id=final_threat_id,
        tool_ids=tool_ids,
        reference_ids=reference_ids,
    )

    await _ensure_not_duplicate(
        objective_id=objective_id,
        action_test_case=action_test_case,
        excluding_test_case_id=test_case_id,
    )

    scalar_fields = {
        "category_id",
        "objective_id",
        "protocol_id",
        "attack_vector_id",
        "test_type_id",
        "severity_id",
        "threat_id",
        "test_case_name",
        "pre_condition",
        "impact",
        "action_test_case",
        "test_case_name",
        "pre_condition",
        "impact",
        "description",
        "attack_path",
        "test_steps",
        "expected_output",
        "attack_feasibility",
        "cia_impact",
        "safety_impact",
    }

    text_fields = {
        "description",
        "attack_path",
        "test_steps",
        "expected_output",
        "attack_feasibility",
        "cia_impact",
        "safety_impact",
    }

    update_data: dict = {}

    for field_name, value in supplied.items():
        if field_name not in scalar_fields:
            continue

        if field_name == "action_test_case":
            update_data[field_name] = action_test_case
        elif field_name in text_fields:
            update_data[field_name] = _clean_optional_text(
                value
            )
        else:
            update_data[field_name] = value

    update_data["updated_by"] = int(
        current_admin.id
    )

    async with db.tx() as transaction:
        await transaction.test_cases.update(
            where={
                "id": test_case_id,
            },
            data=update_data,
        )

        if payload.tool_ids is not None:
            await transaction.test_case_tools.delete_many(
                where={
                    "test_case_id": test_case_id,
                }
            )

            for tool_id in tool_ids:
                await transaction.test_case_tools.create(
                    data={
                        "test_case_id": test_case_id,
                        "tool_id": tool_id,
                    }
                )

        if payload.reference_ids is not None:
            await transaction.test_case_references.delete_many(
                where={
                    "test_case_id": test_case_id,
                }
            )

            for reference_id in reference_ids:
                await transaction.test_case_references.create(
                    data={
                        "test_case_id": test_case_id,
                        "reference_id": reference_id,
                    }
                )

    updated = await _get_active_test_case(
        test_case_id
    )

    return _map_test_case(updated)


@router.delete(
    "/test-cases/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_admin_test_case(
    test_case_id: int,
    current_admin=Depends(require_admin),
):
    await _get_active_test_case(
        test_case_id
    )

    await db.test_cases.update(
        where={
            "id": test_case_id,
        },
        data={
            "deleted_at": datetime.now(timezone.utc),
            "deleted_by": int(current_admin.id),
            "updated_by": int(current_admin.id),
        },
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.get(
    "/stats",
    response_model=AdminStatsRead,
)
async def get_admin_stats(
    _current_admin=Depends(require_admin),
):
    seven_days_ago = (
        datetime.now(timezone.utc)
        - timedelta(days=7)
    )

    total_test_cases = await db.test_cases.count(
        where={
            "deleted_at": None,
        }
    )

    total_users = await db.users.count()

    recent_updates = await db.test_cases.count(
        where={
            "deleted_at": None,
            "updated_at": {
                "gte": seven_days_ago,
            },
        }
    )

    return {
        "total_test_cases": total_test_cases,
        "total_users": total_users,
        "recent_updates": recent_updates,
    }


@router.get(
    "/field-suggestions",
    response_model=FieldSuggestions,
)
async def get_field_suggestions(
    _current_admin=Depends(require_admin),
):
    """
    Return distinct previously-used values for every free-text
    field so the admin form can offer them as quick-pick options.
    """

    TEXT_FIELDS = [
        "description",
        "attack_path",
        "test_steps",
        "expected_output",
        "attack_feasibility",
        "cia_impact",
        "safety_impact",
    ]

    result: dict[str, list[str]] = {}

    for field in TEXT_FIELDS:
        # Fetch all non-deleted rows that have a value for this field,
        # then deduplicate in Python (more portable than relying on
        # Prisma Python's distinct + where combination).
        rows = await db.test_cases.find_many(
            where={
                "deleted_at": None,
                field: {
                    "not": None,
                },
            },
            # Only select the field we need to keep payloads small
        )
        seen: set[str] = set()
        for row in rows:
            raw = getattr(row, field, None)
            if raw is not None:
                stripped = str(raw).strip()
                if stripped:
                    seen.add(stripped)
        result[field] = sorted(seen)

    return result


@router.post(
    "/lookups/{lookup_type}",
    response_model=LookupItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_lookup_item(
    lookup_type: str,
    payload: CreateLookupItemPayload,
    _current_admin=Depends(require_admin),
):
    """
    Create a new entry in the requested lookup table.
    Supports all admin lookup tables, including category/objective/severity
    creation with their required relation metadata.
    """

    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name is required",
        )

    if lookup_type == "categories":
        existing = await db.categories.find_first(where={"name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.categories.create(data={"name": name})
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "objectives":
        if payload.category_id is None:
            raise HTTPException(status_code=422, detail="Category is required for a new objective")
        existing = await db.objectives.find_first(
            where={"category_id": payload.category_id, "name": name}
        )
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.objectives.create(
            data={"category_id": payload.category_id, "name": name}
        )
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "severities":
        if payload.severity_rank is None:
            raise HTTPException(status_code=422, detail="Severity rank is required")
        existing = await db.severities.find_first(where={"name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.severities.create(
            data={"name": name, "severity_rank": payload.severity_rank}
        )
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "protocols":
        # Check for duplicate
        existing = await db.protocols.find_first(where={"name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.protocols.create(data={"name": name})
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "attack_vectors":
        existing = await db.attack_vectors.find_first(where={"name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.attack_vectors.create(data={"name": name})
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "test_types":
        existing = await db.test_types.find_first(where={"name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.name}
        item = await db.test_types.create(data={"name": name})
        return {"id": int(item.id), "name": item.name}

    elif lookup_type == "threats":
        existing = await db.threats.find_first(where={"threat_text": name})
        if existing:
            return {"id": int(existing.id), "name": existing.threat_text}
        item = await db.threats.create(data={"threat_text": name})
        return {"id": int(item.id), "name": item.threat_text}


    elif lookup_type == "tools":
        existing = await db.tools_master.find_first(where={"tool_name": name})
        if existing:
            return {"id": int(existing.id), "name": existing.tool_name}
        item = await db.tools_master.create(data={"tool_name": name})
        return {"id": int(item.id), "name": item.tool_name}

    elif lookup_type == "references":
        existing = await db.references_master.find_first(where={"ref_text": name})
        if existing:
            return {"id": int(existing.id), "name": existing.ref_text}
        item = await db.references_master.create(data={"ref_text": name})
        return {"id": int(item.id), "name": item.ref_text}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown lookup type: {lookup_type!r}. Supported: protocols, attack_vectors, test_types, threats, tools, references",
        )