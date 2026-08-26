from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import LONGTEXT
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
    ecu_detail: Mapped["ProjectEcuDetail | None"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
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


class ProjectEcuDetail(Base):
    """ECU Details for a project."""

    __tablename__ = "project_ecu_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True, unique=True
    )
    ecu_name: Mapped[str] = mapped_column(String(255), nullable=False)
    part_number: Mapped[str] = mapped_column(String(255), nullable=False)
    ecu_risk_rating: Mapped[str] = mapped_column(String(100), nullable=False)
    architecture: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_line: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    microcontroller_cpu_provider: Mapped[str] = mapped_column(String(255), nullable=False)
    date_hardware_b_sample_available: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_harness_available: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_production_intent_software_available: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    export_control_classification: Mapped[str] = mapped_column(String(255), nullable=False)
    pentest_provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="ecu_detail")


# Test Case Related Models
class Category(Base):
    """Test category."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    objectives: Mapped[list["Objective"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Objective(Base):
    """Test objective under a category."""

    __tablename__ = "objectives"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uk_obj"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped["Category"] = relationship(back_populates="objectives")
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="objective", cascade="all, delete-orphan"
    )


class Protocol(Base):
    """Communication protocol."""

    __tablename__ = "protocols"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="protocol", cascade="all, delete-orphan"
    )


class AttackVector(Base):
    """Attack vector."""

    __tablename__ = "attack_vectors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="attack_vector", cascade="all, delete-orphan"
    )


class TestType(Base):
    """Test type."""

    __tablename__ = "test_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="test_type", cascade="all, delete-orphan"
    )


class Severity(Base):
    """Severity level."""

    __tablename__ = "severities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    severity_rank: Mapped[int] = mapped_column(Integer, nullable=False)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="severity", cascade="all, delete-orphan"
    )


class Threat(Base):
    """Threat."""

    __tablename__ = "threats"
    __table_args__ = (UniqueConstraint("threat_text", name="uk_threat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    threat_text: Mapped[str] = mapped_column(Text, nullable=False)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="threat", cascade="all, delete-orphan"
    )


class Asset(Base):
    """Asset."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class ToolMaster(Base):
    """Tool master."""

    __tablename__ = "tools_master"
    __table_args__ = (UniqueConstraint("tool_name", name="uk_tool"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tool_name: Mapped[str] = mapped_column(String(1000), nullable=False)

    test_case_tools: Mapped[list["TestCaseTool"]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )


class ReferenceMaster(Base):
    """Reference master."""

    __tablename__ = "references_master"
    __table_args__ = (UniqueConstraint("ref_text", name="uk_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ref_text: Mapped[str] = mapped_column(Text, nullable=False)

    test_case_references: Mapped[list["TestCaseReference"]] = relationship(
        back_populates="reference", cascade="all, delete-orphan"
    )


class TestCase(Base):
    """Test case."""

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    objective_id: Mapped[int] = mapped_column(
        ForeignKey("objectives.id"), nullable=False, index=True
    )
    protocol_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id"), nullable=True)
    attack_vector_id: Mapped[int | None] = mapped_column(
        ForeignKey("attack_vectors.id"), nullable=True
    )
    test_type_id: Mapped[int | None] = mapped_column(ForeignKey("test_types.id"), nullable=True)
    severity_id: Mapped[int | None] = mapped_column(ForeignKey("severities.id"), nullable=True)
    threat_id: Mapped[int | None] = mapped_column(ForeignKey("threats.id"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)

    action_test_case: Mapped[str] = mapped_column(LONGTEXT, nullable=False)
    source_scope_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    attack_path: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    test_steps: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    attack_feasibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    cia_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    automation_possible: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="test_cases")
    objective: Mapped["Objective"] = relationship(back_populates="test_cases")
    protocol: Mapped["Protocol | None"] = relationship(back_populates="test_cases")
    attack_vector: Mapped["AttackVector | None"] = relationship(back_populates="test_cases")
    test_type: Mapped["TestType | None"] = relationship(back_populates="test_cases")
    severity: Mapped["Severity | None"] = relationship(back_populates="test_cases")
    threat: Mapped["Threat | None"] = relationship(back_populates="test_cases")
    asset: Mapped["Asset | None"] = relationship(back_populates="test_cases")

    test_case_tools: Mapped[list["TestCaseTool"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )
    test_case_references: Mapped[list["TestCaseReference"]] = relationship(
        back_populates="test_case", cascade="all, delete-orphan"
    )


class TestCaseTool(Base):
    """Junction table for test cases and tools."""

    __tablename__ = "test_case_tools"
    __table_args__ = (PrimaryKeyConstraint("test_case_id", "tool_id"),)

    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools_master.id"), nullable=False)

    test_case: Mapped["TestCase"] = relationship(back_populates="test_case_tools")
    tool: Mapped["ToolMaster"] = relationship(back_populates="test_case_tools")


class TestCaseReference(Base):
    """Junction table for test cases and references."""

    __tablename__ = "test_case_references"
    __table_args__ = (PrimaryKeyConstraint("test_case_id", "reference_id"),)

    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    reference_id: Mapped[int] = mapped_column(ForeignKey("references_master.id"), nullable=False)

    test_case: Mapped["TestCase"] = relationship(back_populates="test_case_references")
    reference: Mapped["ReferenceMaster"] = relationship(back_populates="test_case_references")