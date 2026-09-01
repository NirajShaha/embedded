from fastapi import APIRouter, HTTPException

from app.prisma_client import db
from app.schemas import (
    AttributeGroupRead,
    SelectionsRead,
    SelectionsUpdate,
)

router = APIRouter(tags=["pages"])

MAX_PAGE = 4


def _guard_page(page: int) -> None:
    if page < 1 or page > MAX_PAGE:
        raise HTTPException(
            status_code=400,
            detail="Page must be between 1 and 4",
        )


@router.get(
    "/pages/{page}/attributes",
    response_model=list[AttributeGroupRead],
)
async def page_attributes(page: int):

    _guard_page(page)

    groups = await db.attribute_groups.find_many(
        where={
            "page": page,
        },
        include={
            "attributes": True,
        },
        order={
            "id": "asc",
        },
    )

    return groups


@router.get(
    "/projects/{project_id}/page/{page}/selections",
    response_model=SelectionsRead,
)
async def get_selections(
    project_id: int,
    page: int,
):

    _guard_page(page)

    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    selections = await db.project_selections.find_many(
        where={
            "project_id": project_id,
            "page": page,
        }
    )

    return SelectionsRead(
        page=page,
        attribute_ids=[
            item.attribute_id
            for item in selections
        ],
    )


@router.put(
    "/projects/{project_id}/page/{page}/selections",
    response_model=SelectionsRead,
)
async def update_selections(
    project_id: int,
    page: int,
    payload: SelectionsUpdate,
):

    _guard_page(page)

    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    attribute_ids = sorted(
        set(payload.attribute_ids)
    )

    if attribute_ids:

        attributes = await db.attributes.find_many(
            where={
                "id": {
                    "in": attribute_ids,
                },
            }
        )

        found_ids = {
            attr.id
            for attr in attributes
        }

        if set(attribute_ids) != found_ids:
            raise HTTPException(
                status_code=400,
                detail="One or more attributes do not exist",
            )

    await db.project_selections.delete_many(
        where={
            "project_id": project_id,
            "page": page,
        }
    )

    for attribute_id in attribute_ids:

        await db.project_selections.create(
            data={
                "project_id": project_id,
                "attribute_id": attribute_id,
                "page": page,
            }
        )

    return SelectionsRead(
        page=page,
        attribute_ids=attribute_ids,
    )