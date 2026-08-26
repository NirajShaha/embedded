from fastapi import APIRouter, Depends, HTTPException
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
    category_id: int | None = None,
    test_type_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TestCase]:
    """
    List test cases, optionally filtered by category and/or test type.
    """
    from app.models import TestCaseTool, TestCaseReference
    
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

    if category_id is not None:
        # Verify category exists
        category = await db.get(Category, category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        query = query.where(TestCase.category_id == category_id)

    if test_type_id is not None:
        # Verify test type exists
        test_type = await db.get(TestType, test_type_id)
        if test_type is None:
            raise HTTPException(status_code=404, detail="Test type not found")
        query = query.where(TestCase.test_type_id == test_type_id)

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
