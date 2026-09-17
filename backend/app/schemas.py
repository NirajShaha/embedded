from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AttributeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AttributeGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    attributes: list[AttributeRead]


class SelectionsRead(BaseModel):
    page: int
    attribute_ids: list[int]


class SelectionsUpdate(BaseModel):
    attribute_ids: list[int]


# ECU Detail Schemas
class ProjectEcuDetailCreate(BaseModel):
    ecu_name: str = Field(min_length=1, max_length=255)
    part_number: str = Field(min_length=1, max_length=255)
    ecu_risk_rating: str = Field(min_length=1, max_length=100)
    architecture: str = Field(min_length=1, max_length=255)
    vehicle_line: str = Field(min_length=1, max_length=255)
    year: int = Field(ge=1900, le=2100)
    microcontroller_cpu_provider: str = Field(min_length=1, max_length=255)
    date_hardware_b_sample_available: date | None = None
    date_harness_available: date | None = None
    date_production_intent_software_available: date | None = None
    export_control_classification: str = Field(min_length=1, max_length=255)
    pentest_provider_name: str = Field(min_length=1, max_length=255)


class ProjectEcuDetailUpdate(BaseModel):
    ecu_name: str | None = None
    part_number: str | None = None
    ecu_risk_rating: str | None = None
    architecture: str | None = None
    vehicle_line: str | None = None
    year: int | None = None
    microcontroller_cpu_provider: str | None = None
    date_hardware_b_sample_available: date | None = None
    date_harness_available: date | None = None
    date_production_intent_software_available: date | None = None
    export_control_classification: str | None = None
    pentest_provider_name: str | None = None


class ProjectEcuDetailRead(ProjectEcuDetailCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


# Test Case Related Schemas
class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ObjectiveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_id: int


class ProtocolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AttackVectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TestTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SeverityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    severity_rank: int


class ThreatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    threat_text: str


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_name: str


class ToolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_name: str


class ReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ref_text: str


class TestCaseToolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tool: ToolRead


class TestCaseReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference: ReferenceRead


class TestCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    objective_id: int
    protocol_id: int | None
    attack_vector_id: int | None
    test_type_id: int | None
    severity_id: int | None
    threat_id: int | None
    asset_id: int | None

    action_test_case: str
    source_scope_status: str | None
    description: str | None
    attack_path: str | None
    test_steps: str | None
    expected_output: str | None
    attack_feasibility: str | None
    cia_impact: str | None
    safety_impact: str | None
    automation_possible: str | None

    created_at: datetime

    category: CategoryRead | None
    objective: ObjectiveRead | None
    protocol: ProtocolRead | None
    attack_vector: AttackVectorRead | None
    test_type: TestTypeRead | None
    severity: SeverityRead | None
    threat: ThreatRead | None
    asset: AssetRead | None
    test_case_tools: list[TestCaseToolRead]
    test_case_references: list[TestCaseReferenceRead]

    is_overridden: bool = False


class TestCaseOverrideUpdate(BaseModel):
    """Per-project edits to a test case.

    ``None`` means "leave as-is". The text fields are written verbatim, so an empty
    string explicitly clears the master value for this project. ``tools`` and
    ``references`` are full replacement sets; ``None`` keeps the master links and an
    empty list removes them all.
    """

    action_test_case: str | None = None
    source_scope_status: str | None = None
    description: str | None = None
    attack_path: str | None = None
    test_steps: str | None = None
    expected_output: str | None = None
    attack_feasibility: str | None = None
    cia_impact: str | None = None
    safety_impact: str | None = None
    automation_possible: str | None = None

    tools: list[int] | None = None
    references: list[int] | None = None


# Authentication schemas

UserRole = Literal[
    "ADMIN",
    "USER",
]


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        min_length=1,
        max_length=255,
    )


class AuthUserRead(BaseModel):
    id: int
    username: str
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead


# Admin test-case write schemas

AutomationOption = Literal[
    "Yes",
    "No",
    "Partial",
]


class TestCaseCreate(BaseModel):
    category_id: int = Field(gt=0)
    objective_id: int = Field(gt=0)

    protocol_id: int | None = Field(
        default=None,
        gt=0,
    )

    attack_vector_id: int | None = Field(
        default=None,
        gt=0,
    )

    test_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    severity_id: int | None = Field(
        default=None,
        gt=0,
    )

    threat_id: int | None = Field(
        default=None,
        gt=0,
    )

    asset_id: int | None = Field(
        default=None,
        gt=0,
    )

    action_test_case: str = Field(
        min_length=1,
    )

    source_scope_status: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None
    attack_path: str | None = None
    test_steps: str | None = None
    expected_output: str | None = None
    attack_feasibility: str | None = None
    cia_impact: str | None = None
    safety_impact: str | None = None

    automation_possible: AutomationOption | None = None

    tool_ids: list[int] = Field(
        default_factory=list,
    )

    reference_ids: list[int] = Field(
        default_factory=list,
    )


class TestCaseUpdate(BaseModel):
    category_id: int | None = Field(
        default=None,
        gt=0,
    )

    objective_id: int | None = Field(
        default=None,
        gt=0,
    )

    protocol_id: int | None = Field(
        default=None,
        gt=0,
    )

    attack_vector_id: int | None = Field(
        default=None,
        gt=0,
    )

    test_type_id: int | None = Field(
        default=None,
        gt=0,
    )

    severity_id: int | None = Field(
        default=None,
        gt=0,
    )

    threat_id: int | None = Field(
        default=None,
        gt=0,
    )

    asset_id: int | None = Field(
        default=None,
        gt=0,
    )

    action_test_case: str | None = Field(
        default=None,
        min_length=1,
    )

    source_scope_status: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None
    attack_path: str | None = None
    test_steps: str | None = None
    expected_output: str | None = None
    attack_feasibility: str | None = None
    cia_impact: str | None = None
    safety_impact: str | None = None

    automation_possible: AutomationOption | None = None

    tool_ids: list[int] | None = None
    reference_ids: list[int] | None = None


class LookupItem(BaseModel):
    id: int
    name: str


class ObjectiveLookupItem(LookupItem):
    category_id: int


class SeverityLookupItem(LookupItem):
    severity_rank: int


class TestCaseLookups(BaseModel):
    categories: list[LookupItem]
    objectives: list[ObjectiveLookupItem]
    protocols: list[LookupItem]
    attack_vectors: list[LookupItem]
    test_types: list[LookupItem]
    severities: list[SeverityLookupItem]
    threats: list[LookupItem]
    assets: list[LookupItem]
    tools: list[LookupItem]
    references: list[LookupItem]


class AdminStatsRead(BaseModel):
    total_test_cases: int
    total_users: int
    recent_updates: int


class FieldSuggestions(BaseModel):
    """Distinct previously-used values for each free-text field in test_cases."""
    source_scope_status: list[str] = []
    description: list[str] = []
    attack_path: list[str] = []
    test_steps: list[str] = []
    expected_output: list[str] = []
    attack_feasibility: list[str] = []
    cia_impact: list[str] = []
    safety_impact: list[str] = []


class CreateLookupItemPayload(BaseModel):
    """Payload for on-the-fly lookup item creation from the admin form."""
    name: str = Field(min_length=1, max_length=500)
