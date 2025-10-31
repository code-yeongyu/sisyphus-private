from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# === Enums ===
class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class RetrievalType(str, Enum):
    keywords = "keywords"
    prompt = "prompt"


# === v2.1 Verification Classes ===
class BashVerification(BaseModel):
    execute: str
    expected_stdout: str | None = None
    expected_stderr: str | None = None
    expected_exit_code: int = 0
    notes: str | None = None


class LLMJudgeBy(str, Enum):
    ORCHESTRATOR = "orchestrator-agent"
    EXTERNAL = "external-agent"


class LLMJudgeVerification(BaseModel):
    by: LLMJudgeBy = LLMJudgeBy.ORCHESTRATOR
    context_commands: list[str] = []
    instruction: str


# === Reference Retrieval Discriminated Union ===
class KeywordsRetrieval(BaseModel):
    type: Literal["keywords"]
    keywords: list[str]
    line_range: list[int] | None = None


class PromptRetrieval(BaseModel):
    type: Literal["prompt"]
    prompt: str


RetrievalSpec = Annotated[
    KeywordsRetrieval | PromptRetrieval,
    Field(discriminator="type"),
]


# === Verification ===
class VerificationItem(BaseModel):
    id: str
    title: str
    description: str
    verified: bool = False
    verified_at: str | None = None
    verification_evidence: str | None = None
    orchestrator_manually_verified: bool
    manual_verification_evidence: str
    bash: list[BashVerification] = []
    llm_judge: list[LLMJudgeVerification] = []

    @model_validator(mode="after")
    def validate_at_least_one(self) -> Self:
        if not self.bash and not self.llm_judge:
            raise ValueError("bash 또는 llm_judge 중 하나 이상 필수")
        return self


# === Reference Discriminated Union (모든 타입) ===
class ReferencePointer(BaseModel):
    type: Literal["pointer"]
    ref_id: str
    notes: str | None = None


class FileReference(BaseModel):
    type: Literal["file"]
    path: str
    description: str
    retrieval: RetrievalSpec | None = None
    notes: str | None = None
    id: str | None = None


class URLReference(BaseModel):
    type: Literal["url"]
    url: str
    description: str
    retrieval: RetrievalSpec | None = None
    notes: str | None = None
    id: str | None = None


class MarkdownReference(BaseModel):
    type: Literal["markdown"]
    description: str
    content: str
    id: str | None = None


ReferenceItem = Annotated[
    ReferencePointer | FileReference | URLReference | MarkdownReference,
    Field(discriminator="type"),
]


# === Todo (Recursive - 모든 필드) ===
class Todo(BaseModel):
    id: str | int
    title: str
    status: TodoStatus
    parallel_group: int | None = None
    created_at: str
    updated_at: str
    status_changed_at: str | None = None
    references: list[ReferenceItem] = []
    details: dict[str, Any] = {}
    verification_spec: list[VerificationItem] = []
    children: list[Todo] = []
    parallel_note: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v: str | int) -> str:
        return str(v)


# === Base Models ===
class Metadata(BaseModel):
    created_at: str
    updated_at: str
    format_version: str = "2.0"


class UserRequest(BaseModel):
    original: str
    created_at: str
    additional: list[str] = []


class DetailedObjective(BaseModel):
    goal: str
    measurable: str


class Objectives(BaseModel):
    core: str
    detailed: list[DetailedObjective] = []


class Background(BaseModel):
    current_situation: str
    reason_for_change: str
    changes_to_make: str


class RequiredBackground(BaseModel):
    description: str
    file_structure: str | None = None
    references: list[ReferenceItem] = []


class ExecutionStatus(BaseModel):
    started: bool
    completed: bool
    started_at: str | None = None
    completed_at: str | None = None


class WorkMode(BaseModel):
    parallel_requested: bool
    current_task_id: str | None = None


class Progress(BaseModel):
    total_tasks: int
    completed: int
    in_progress: int
    pending: int


class Status(BaseModel):
    execution: ExecutionStatus
    work_mode: WorkMode
    progress: Progress
    current_work: str


class Workflow(BaseModel):
    dependency_diagram: str
    critical_path: list[str] = []


class UserScenario(BaseModel):
    scenario: str
    experience: str


class BusinessMetric(BaseModel):
    metric: str
    target: str


class TechnicalCriterion(BaseModel):
    category: str
    criteria: str
    command: str | None = None
    expected: str


class SuccessVision(BaseModel):
    user_perspective: list[UserScenario] = []
    business_perspective: list[BusinessMetric] = []
    technical_criteria: list[TechnicalCriterion] = []


class FinalVerificationItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    verified: bool = False
    verified_at: str | None = None
    verification_evidence: str | None = None
    orchestrator_manually_verified: bool
    manual_verification_evidence: str
    bash: list[BashVerification] = []
    llm_judge: list[LLMJudgeVerification] = []

    @model_validator(mode="after")
    def validate_at_least_one(self) -> Self:
        if not self.bash and not self.llm_judge:
            raise ValueError("bash 또는 llm_judge 중 하나 이상 필수")
        return self


# === Root Model (모든 필드) ===
class WorkPlan(BaseModel):
    model_config = ConfigDict(extra="allow")

    metadata: Metadata
    user_request: UserRequest
    objectives: Objectives
    background: Background
    required_background: RequiredBackground
    status: Status
    workflow: Workflow
    todos: list[Todo]
    success_vision: SuccessVision
    final_verification: list[FinalVerificationItem]
