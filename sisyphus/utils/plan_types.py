from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# === Enums ===
class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class ReferenceType(str, Enum):
    file = "file"
    url = "url"
    code_snippet = "code_snippet"
    text = "text"


class InputType(str, Enum):
    command = "command"
    prompt = "prompt"
    manual = "manual"
    multi_command = "multi_command"


class VerifyType(str, Enum):
    programmatic = "programmatic"
    llm_judge = "llm_judge"
    none = "none"
    prompt = "prompt"


class RetrievalType(str, Enum):
    keywords = "keywords"
    prompt = "prompt"


# === Input Discriminated Union (모든 타입) ===
class CommandInput(BaseModel):
    type: Literal["command"]
    command: str
    capture_output: bool = True


class PromptInput(BaseModel):
    type: Literal["prompt"]
    prompt: str
    context: dict[str, Any] = {}


class ManualInput(BaseModel):
    type: Literal["manual"]
    instructions: str


class MultiCommandInput(BaseModel):
    type: Literal["multi_command"]
    commands: list[str]


InputSpec = Annotated[
    CommandInput | PromptInput | ManualInput | MultiCommandInput,
    Field(discriminator="type"),
]


# === Verify Discriminated Union (모든 타입) ===
class ProgrammaticVerify(BaseModel):
    type: Literal["programmatic"]
    method: str  # "contains", "exact", "regex", "exit_code"
    expected: str | int


class LLMJudgeVerify(BaseModel):
    type: Literal["llm_judge"]
    criteria: list[str] = []
    accept_if: str = "All criteria met"


class NoneVerify(BaseModel):
    type: Literal["none"]


class PromptVerify(BaseModel):
    type: Literal["prompt"]
    prompt: str


VerifySpec = Annotated[
    ProgrammaticVerify | LLMJudgeVerify | NoneVerify | PromptVerify,
    Field(discriminator="type"),
]


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
    description: str
    input: InputSpec
    verify: VerifySpec
    note: str | None = None
    completed: bool = False


# === Reference Discriminated Union (모든 타입) ===
class FileReference(BaseModel):
    type: Literal["file"] = "file"
    path: str
    description: str
    retrieval: RetrievalSpec | None = None
    notes: str | None = None


class URLReference(BaseModel):
    type: Literal["url"] = "url"
    url: str
    description: str
    retrieval: RetrievalSpec | None = None
    notes: str | None = None


class CodeSnippetReference(BaseModel):
    type: Literal["code_snippet"] = "code_snippet"
    language: str
    description: str
    code: str


class TextReference(BaseModel):
    type: Literal["text"] = "text"
    description: str
    content: str


ReferenceSpec = Annotated[
    FileReference | URLReference | CodeSnippetReference | TextReference,
    Field(discriminator="type"),
]


# === Simple Reference (todo에서 ref_id만 참조) ===
class SimpleReference(BaseModel):
    ref_id: str
    note: str | None = None


# === Todo (Recursive - 모든 필드) ===
class Todo(BaseModel):
    id: str  # "1", "1.1", "1.1.1" (모두 string)
    title: str
    status: TodoStatus
    parallel_group: int | None = None
    created_at: str
    updated_at: str
    status_changed_at: str | None = None
    references: list[SimpleReference] = []
    details: dict[str, Any] = {}
    verification_spec: list[VerificationItem] = []
    children: list[Todo] = []  # Recursive!


# === Base Models ===
class Metadata(BaseModel):
    created_at: str
    updated_at: str
    format_version: str = "2.0"


class UserRequest(BaseModel):
    original: str
    timestamp: str
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
    references: list[ReferenceSpec] = []


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
    description: str
    input: InputSpec
    verify: VerifySpec
    note: str | None = None


class FinalVerificationCategory(BaseModel):
    category: str
    items: list[FinalVerificationItem]


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
    final_verification: list[FinalVerificationCategory]
