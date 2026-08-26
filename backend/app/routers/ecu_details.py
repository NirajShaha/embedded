from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Project, ProjectEcuDetail
from app.schemas import ProjectEcuDetailCreate, ProjectEcuDetailRead, ProjectEcuDetailUpdate

router = APIRouter(prefix="/projects/{project_id}/ecu-detail", tags=["ecu-details"])


@router.get("", response_model=ProjectEcuDetailRead)
async def get_ecu_detail(
    project_id: int, db: AsyncSession = Depends(get_db)
) -> ProjectEcuDetail:
    # Check if project exists
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.scalars(
        select(ProjectEcuDetail).where(ProjectEcuDetail.project_id == project_id)
    )
    ecu_detail = result.first()
    if ecu_detail is None:
        raise HTTPException(status_code=404, detail="ECU detail not found for this project")
    return ecu_detail


@router.post("", response_model=ProjectEcuDetailRead, status_code=status.HTTP_201_CREATED)
async def create_ecu_detail(
    project_id: int,
    payload: ProjectEcuDetailCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectEcuDetail:
    # Check if project exists
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if ECU detail already exists for this project
    existing = await db.scalars(
        select(ProjectEcuDetail).where(ProjectEcuDetail.project_id == project_id)
    )
    if existing.first() is not None:
        raise HTTPException(
            status_code=409, detail="ECU detail already exists for this project"
        )

    ecu_detail = ProjectEcuDetail(project_id=project_id, **payload.model_dump())
    db.add(ecu_detail)
    await db.commit()
    await db.refresh(ecu_detail)
    return ecu_detail


@router.put("", response_model=ProjectEcuDetailRead)
async def update_ecu_detail(
    project_id: int,
    payload: ProjectEcuDetailUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectEcuDetail:
    # Check if project exists
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get existing ECU detail
    result = await db.scalars(
        select(ProjectEcuDetail).where(ProjectEcuDetail.project_id == project_id)
    )
    ecu_detail = result.first()
    if ecu_detail is None:
        raise HTTPException(status_code=404, detail="ECU detail not found for this project")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ecu_detail, field, value)

    await db.commit()
    await db.refresh(ecu_detail)
    return ecu_detail
