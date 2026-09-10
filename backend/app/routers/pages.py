from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth import get_current_user
from app.prisma_client import db
from app.schemas import (
    AttributeGroupRead,
    SelectionsRead,
    SelectionsUpdate,
)


router = APIRouter(
    tags=["pages"],
)


MIN_PAGE = 1
MAX_PAGE = 4


def _guard_page(
    page: int,
) -> None:
    """
    Ensure that the requested page is part of the
    supported embedded configuration workflow.
    """

    if (
        page < MIN_PAGE
        or page > MAX_PAGE
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Page must be between "
                f"{MIN_PAGE} and {MAX_PAGE}"
            ),
        )


async def _ensure_project_exists(
    project_id: int,
):
    """
    Return the requested project or raise 404.
    """

    project = await db.projects.find_unique(
        where={
            "id": project_id,
        }
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


def _normalize_attribute_ids(
    attribute_ids: list[int],
) -> list[int]:
    """
    Remove duplicate IDs, reject invalid IDs,
    and return a deterministic sorted list.
    """

    if any(
        attribute_id <= 0
        for attribute_id
        in attribute_ids
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Attribute IDs must be "
                "positive integers"
            ),
        )

    return sorted(
        set(attribute_ids)
    )


@router.get(
    "/pages/{page}/attributes",
    response_model=list[
        AttributeGroupRead
    ],
)
async def page_attributes(
    page: int,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return attribute groups and attributes for
    an authenticated user's configuration page.
    """

    _guard_page(page)

    groups = (
        await db.attribute_groups.find_many(
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
    )

    return groups


@router.get(
    "/projects/{project_id}/page/{page}/selections",
    response_model=SelectionsRead,
)
async def get_selections(
    project_id: int,
    page: int,
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Return the saved attribute selections for
    an authenticated user's project and page.
    """

    _guard_page(page)

    await _ensure_project_exists(
        project_id
    )

    selections = (
        await db.project_selections.find_many(
            where={
                "project_id": project_id,
                "page": page,
            },
            order={
                "attribute_id": "asc",
            },
        )
    )

    return SelectionsRead(
        page=page,
        attribute_ids=[
            int(
                selection.attribute_id
            )
            for selection
            in selections
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
    _current_user=Depends(
        get_current_user
    ),
):
    """
    Replace the saved selections for the requested
    project and configuration page.

    An empty attribute_ids list clears all selections
    for the requested page.
    """

    _guard_page(page)

    await _ensure_project_exists(
        project_id
    )

    attribute_ids = (
        _normalize_attribute_ids(
            payload.attribute_ids
        )
    )

    if attribute_ids:
        attributes = (
            await db.attributes.find_many(
                where={
                    "id": {
                        "in": (
                            attribute_ids
                        ),
                    },
                },
                include={
                    "attribute_groups": True,
                },
            )
        )

        found_attribute_ids = {
            int(attribute.id)
            for attribute in attributes
        }

        requested_attribute_ids = set(
            attribute_ids
        )

        missing_attribute_ids = sorted(
            requested_attribute_ids
            - found_attribute_ids
        )

        if missing_attribute_ids:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "One or more selected "
                    "attributes do not exist"
                ),
            )

        attributes_from_other_pages = [
            int(attribute.id)
            for attribute in attributes
            if (
                attribute.attribute_groups
                is None
                or int(
                    attribute
                    .attribute_groups
                    .page
                )
                != page
            )
        ]

        if attributes_from_other_pages:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "One or more selected "
                    "attributes do not belong "
                    "to the requested page"
                ),
            )

    async with db.tx() as transaction:
        await (
            transaction
            .project_selections
            .delete_many(
                where={
                    "project_id": (
                        project_id
                    ),
                    "page": page,
                }
            )
        )

        for attribute_id in (
            attribute_ids
        ):
            await (
                transaction
                .project_selections
                .create(
                    data={
                        "project_id": (
                            project_id
                        ),
                        "attribute_id": (
                            attribute_id
                        ),
                        "page": page,
                    }
                )
            )

    return SelectionsRead(
        page=page,
        attribute_ids=attribute_ids,
    )