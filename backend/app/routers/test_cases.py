from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Category, TestCase, TestType
from app.schemas import TestCaseRead

router = APIRouter(prefix="/test-cases", tags=["test-cases"])


@router.get("/categories", response_model=list[dict])
async def get_categories(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Get all test categories."""
    result = await db.scalars(
        select(Category).order_by(Category.name)
    )
    categories = list(result)
    return [
        {"id": cat.id, "name": cat.name}
        for cat in categories
    ]


@router.get("/types", response_model=list[dict])
async def get_test_types(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Get all test types."""
    result = await db.scalars(
        select(TestType).order_by(TestType.name)
    )
    test_types = list(result)
    return [
        {"id": tt.id, "name": tt.name}
        for tt in test_types
    ]


@router.get("", response_model=list[TestCaseRead])
async def list_test_cases(
    category_ids: list[int] | None = Query(default=None),
    test_type_ids: list[int] | None = Query(default=None),
    category_id: int | None = Query(default=None, deprecated=True),
    test_type_id: int | None = Query(default=None, deprecated=True),
    db: AsyncSession = Depends(get_db),
) -> list[TestCase]:
    """
    List test cases, optionally filtered by categories and/or test types.

    Accepts either the new plural params (e.g. ``?category_ids=1&category_ids=2``)
    or the deprecated singular params for backward compatibility.

    A test type named "Both" (case-insensitive) is treated as a wildcard:
    when it is included in the filter, the test_type filter is disabled so
    that test cases of every test type are returned. This matches the
    domain semantics where "Both" means "testable both manually and
    automatically".
    """
    from app.models import TestCaseTool, TestCaseReference

    effective_category_ids: list[int] = []
    if category_ids:
        effective_category_ids.extend(category_ids)
    if category_id is not None and category_id not in effective_category_ids:
        effective_category_ids.append(category_id)

    effective_test_type_ids: list[int] = []
    if test_type_ids:
        effective_test_type_ids.extend(test_type_ids)
    if test_type_id is not None and test_type_id not in effective_test_type_ids:
        effective_test_type_ids.append(test_type_id)

    # Treat "Both" as a wildcard for the test_type filter.
    if effective_test_type_ids:
        both_row = await db.scalar(
            select(TestType).where(TestType.name.ilike("Both"))
        )
        if both_row is not None and both_row.id in effective_test_type_ids:
            effective_test_type_ids = []

    query = select(TestCase).options(
        selectinload(TestCase.category),
        selectinload(TestCase.objective),
        selectinload(TestCase.protocol),
        selectinload(TestCase.attack_vector),
        selectinload(TestCase.test_type),
        selectinload(TestCase.severity),
        selectinload(TestCase.threat),
        selectinload(TestCase.asset),
        selectinload(TestCase.test_case_tools).selectinload(TestCaseTool.tool),
        selectinload(TestCase.test_case_references).selectinload(TestCaseReference.reference),
    )

    if effective_category_ids:
        query = query.where(TestCase.category_id.in_(effective_category_ids))

    if effective_test_type_ids:
        query = query.where(TestCase.test_type_id.in_(effective_test_type_ids))

    result = await db.scalars(query.order_by(TestCase.id))
    return list(result)


@router.get("/{test_case_id}", response_model=TestCaseRead)
async def get_test_case(
    test_case_id: int,
    db: AsyncSession = Depends(get_db),
) -> TestCase:
    """Get a specific test case by ID."""
    test_case = await db.get(TestCase, test_case_id)
    if test_case is None:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case
