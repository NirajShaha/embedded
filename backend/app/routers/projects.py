from fastapi import APIRouter, HTTPException, status

from app.prisma_client import db
from app.schemas import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects():
    projects = await db.projects.find_many(
        order={
            "created_at": "desc"
        }
    )

    return [
        ProjectRead.model_validate(project)
        for project in projects
    ]

@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate):
    project = await db.projects.create(
        data={
            "name": payload.name,
            "description": payload.description,
        }
    )
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int):
    project = await db.projects.find_unique(
        where={
            "id": project_id
        }
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project);