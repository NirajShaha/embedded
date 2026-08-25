from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    selections: Mapped[list["ProjectSelection"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class AttributeGroup(Base):
    """A 'main attribute' belonging to a single selection page."""

    __tablename__ = "attribute_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    page: Mapped[int] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    attributes: Mapped[list["Attribute"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", order_by="Attribute.id"
    )


class Attribute(Base):
    """A 'sub attribute' under a main attribute (AttributeGroup)."""

    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("attribute_groups.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    group: Mapped["AttributeGroup"] = relationship(back_populates="attributes")


class ProjectSelection(Base):
    """One chosen sub-attribute for a project on a given page."""

    __tablename__ = "project_selections"
    __table_args__ = (
        UniqueConstraint("project_id", "attribute_id", name="uq_project_attribute"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attributes.id"), nullable=False, index=True
    )
    page: Mapped[int] = mapped_column(nullable=False, index=True)

    project: Mapped["Project"] = relationship(back_populates="selections")