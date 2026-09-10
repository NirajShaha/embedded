from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth import get_current_user
from app.prisma_client import db
from app.schemas import (
    ProjectCreate,
    ProjectRead,
)


router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)


@router.get(
    "",
    response_model=list[ProjectRead],
)
async def list_projects(
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return all projects to an authenticated user.
    """

    projects = await db.projects.find_many(
        order={
            "created_at": "desc",
        }
    )

    return [
        ProjectRead.model_validate(
            project
        )
        for project in projects
    ]


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: ProjectCreate,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Create a project for an authenticated user.
    """

    project_name = (
        payload.name.strip()
    )

    if not project_name:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Project name is required"
            ),
        )

    project_description = (
        payload.description.strip()
        if payload.description
        else None
    )

    project = await db.projects.create(
        data={
            "name": project_name,
            "description": (
                project_description
                or None
            ),
        }
    )

    return ProjectRead.model_validate(
        project
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
)
async def get_project(
    project_id: int,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return a specific project to an authenticated user.
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

    return ProjectRead.model_validate(
        project
    )