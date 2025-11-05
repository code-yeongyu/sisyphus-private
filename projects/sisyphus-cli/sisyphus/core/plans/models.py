from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"


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


class ReferenceItem(BaseModel):
    ref_id: str | None = None
    uri: str | None = None
    inline: str | None = None

    @model_validator(mode="after")
    def validate_exclusivity(self) -> Self:
        if self.uri and self.inline:
            raise ValueError("uri와 inline은 동시에 사용할 수 없습니다")
        if not self.uri and not self.inline and not self.ref_id:
            raise ValueError("ref_id, uri 또는 inline 중 하나는 필수입니다")
        return self


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


class Todo(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: TodoStatus
    children: list[Todo] | None = None
    references: list[ReferenceItem] = []
    verification_spec: list[VerificationItem] = []


class WorkPlan(BaseModel):
    id: str
    name: str
    depends_on: list[str] = []
    todos: list[Todo]
    references: list[ReferenceItem] = []

    execution: ExecutionStatus = Field(
        default_factory=lambda: ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None)
    )
    work_mode: WorkMode = Field(default_factory=lambda: WorkMode(parallel_requested=False, current_task_id=None))
    progress: Progress = Field(default_factory=lambda: Progress(total_tasks=0, completed=0, in_progress=0, pending=0))
    current_work: str = ""


class Metadata(BaseModel):
    created_at: str
    updated_at: str | None = None


class PlanDocument(BaseModel):
    version: str
    metadata: Metadata
    work_plans: list[WorkPlan]
