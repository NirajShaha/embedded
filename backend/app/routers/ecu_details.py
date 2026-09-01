from fastapi import APIRouter, HTTPException, status

from app.prisma_client import db
from app.schemas import (
    ProjectEcuDetailCreate,
    ProjectEcuDetailRead,
    ProjectEcuDetailUpdate
)

from datetime import datetime

router = APIRouter(prefix="/projects/{project_id}/ecu-detail", tags=["ecu-details"])

def _convert_dates(data: dict) -> dict:
    result = {}

    for key, value in data.items():

        if value is None:
            result[key] = None

        elif hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            result[key] = datetime.combine(
                value,
                datetime.min.time()
            )

        else:
            result[key] = value

    return result


@router.get("", response_model=ProjectEcuDetailRead)
async def get_ecu_detail(project_id: int):
    # Check if project exists
    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    ecu_detail = await db.project_ecu_details.find_first(
        where={
            "project_id": project_id
        }
    )
    if ecu_detail is None:
        raise HTTPException(status_code=404, detail="ECU detail not found for this project")
    
    return ecu_detail


@router.post("", response_model=ProjectEcuDetailRead, status_code=status.HTTP_201_CREATED)
async def create_ecu_detail(project_id: int, payload: ProjectEcuDetailCreate):
    # Check if project exists
    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if ECU detail already exists for this project
    existing = await db.project_ecu_details.find_first(
        where={
            "project_id": project_id
        }
    )
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="ECU detail already exists for this project"
        )

    payload_data = _convert_dates(
        payload.model_dump()
    )

    ecu_detail = await db.project_ecu_details.create(
        data={
            "project_id": project_id,
            **payload_data
        }
    )
    return ecu_detail


@router.put("", response_model=ProjectEcuDetailRead)
async def update_ecu_detail(
    project_id: int,
    payload: ProjectEcuDetailUpdate
    ):
    # Check if project exists
    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get existing ECU detail
    existing = await db.project_ecu_details.find_first(
        where={
            "project_id": project_id
        }
    )
    if existing is None:
        raise HTTPException(status_code=404, detail="ECU detail not found for this project")

    # Update only provided fields
    payload_data = _convert_dates(
        payload.model_dump(
            exclude_unset=True
        )
    )

    updated = await db.project_ecu_details.update(
        where={
            "id": existing.id
        },
        data=payload_data
    )
    return updated
