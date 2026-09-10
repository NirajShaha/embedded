from datetime import date, datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth import get_current_user
from app.prisma_client import db
from app.schemas import (
    ProjectEcuDetailCreate,
    ProjectEcuDetailRead,
    ProjectEcuDetailUpdate,
)


router = APIRouter(
    prefix="/projects/{project_id}/ecu-detail",
    tags=["ecu-details"],
)


def _convert_dates(
    data: dict[str, Any],
):
    """
    Convert Pydantic date values into datetime values
    supported by Prisma DateTime fields.

    Existing datetime values are preserved.
    None values are preserved so nullable fields can be cleared.
    """

    result: dict[str, Any] = {}

    for key, value in data.items():
        if value is None:
            result[key] = None

        elif isinstance(
            value,
            datetime,
        ):
            result[key] = value

        elif isinstance(
            value,
            date,
        ):
            result[key] = datetime.combine(
                value,
                datetime.min.time(),
            )

        else:
            result[key] = value

    return result


async def _ensure_project_exists(
    project_id: int,
):
    """
    Return the requested project.

    Raise 404 when the project does not exist.
    """

    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Project not found",
        )

    return project


async def _get_project_ecu_detail(
    project_id: int,
):
    """
    Return the ECU detail associated with the project.

    Raise 404 when ECU details do not exist.
    """

    ecu_detail = (
        await db.project_ecu_details.find_first(
            where={
                "project_id": project_id,
            }
        )
    )

    if ecu_detail is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "ECU detail not found "
                "for this project"
            ),
        )

    return ecu_detail


@router.get(
    "",
    response_model=ProjectEcuDetailRead,
)
async def get_ecu_detail(
    project_id: int,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return ECU details for an authenticated user's project.
    """

    await _ensure_project_exists(
        project_id
    )

    ecu_detail = (
        await _get_project_ecu_detail(
            project_id
        )
    )

    return ecu_detail


@router.post(
    "",
    response_model=ProjectEcuDetailRead,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_ecu_detail(
    project_id: int,
    payload: ProjectEcuDetailCreate,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Create ECU details for an authenticated user's project.

    Each project can have only one ECU-detail record.
    """

    await _ensure_project_exists(
        project_id
    )

    existing = (
        await db.project_ecu_details.find_first(
            where={
                "project_id": project_id,
            }
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "ECU detail already exists "
                "for this project"
            ),
        )

    payload_data = _convert_dates(
        payload.model_dump()
    )

    ecu_detail = (
        await db.project_ecu_details.create(
            data={
                "project_id": project_id,
                **payload_data,
            }
        )
    )

    return ecu_detail


@router.put(
    "",
    response_model=ProjectEcuDetailRead,
)
async def update_ecu_detail(
    project_id: int,
    payload: ProjectEcuDetailUpdate,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Update only the supplied ECU-detail fields.

    An authenticated ADMIN or USER can update ECU details.
    """

    await _ensure_project_exists(
        project_id
    )

    existing = (
        await _get_project_ecu_detail(
            project_id
        )
    )

    payload_data = _convert_dates(
        payload.model_dump(
            exclude_unset=True
        )
    )

    if not payload_data:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "At least one ECU detail field "
                "must be provided for update"
            ),
        )

    updated = (
        await db.project_ecu_details.update(
            where={
                "id": existing.id,
            },
            data=payload_data,
        )
    )

    return updated