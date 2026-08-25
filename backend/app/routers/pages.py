from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Attribute, AttributeGroup, Project, ProjectSelection
from app.schemas import AttributeGroupRead, SelectionsRead, SelectionsUpdate

router = APIRouter(tags=["pages"])

MAX_PAGE = 4


def _guard_page(page: int) -> None:
    if page < 1 or page > MAX_PAGE:
        raise HTTPException(status_code=400, detail="Page must be between 1 and 4")


@router.get("/pages/{page}/attributes", response_model=list[AttributeGroupRead])
async def page_attributes(page: int, db: AsyncSession = Depends(get_db)) -> list[AttributeGroup]:
    _guard_page(page)
    result = await db.scalars(
        select(AttributeGroup)
        .options(selectinload(AttributeGroup.attributes))
        .where(AttributeGroup.page == page)
        .order_by(AttributeGroup.id)
    )
    return list(result)


@router.get(
    "/projects/{project_id}/page/{page}/selections", response_model=SelectionsRead
)
async def get_selections(
    project_id: int, page: int, db: AsyncSession = Depends(get_db)
) -> SelectionsRead:
    _guard_page(page)
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.scalars(
        select(ProjectSelection.attribute_id).where(
            ProjectSelection.project_id == project_id,
            ProjectSelection.page == page,
        )
    )
    return SelectionsRead(page=page, attribute_ids=list(result))


@router.put(
    "/projects/{project_id}/page/{page}/selections", response_model=SelectionsRead
)
async def update_selections(
    project_id: int,
    page: int,
    payload: SelectionsUpdate,
    db: AsyncSession = Depends(get_db),
) -> SelectionsRead:
    _guard_page(page)
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    attribute_ids = sorted(set(payload.attribute_ids))
    if attribute_ids:
        attrs = await db.scalars(select(Attribute).where(Attribute.id.in_(attribute_ids)))
        final_ids = {a.id for a in attrs.all()}
        if set(attribute_ids) != final_ids:
            raise HTTPException(
                status_code=400,
                detail="One or more attributes do not exist",
            )

    await db.execute(
        delete(ProjectSelection).where(
            ProjectSelection.project_id == project_id,
            ProjectSelection.page == page,
        )
    )
    for aid in attribute_ids:
        db.add(
            ProjectSelection(
                project_id=project_id,
                attribute_id=aid,
                page=page,
            )
        )
    await db.commit()

    result = await db.scalars(
        select(ProjectSelection.attribute_id).where(
            ProjectSelection.project_id == project_id,
            ProjectSelection.page == page,
        )
    )
    return SelectionsRead(page=page, attribute_ids=list(result))