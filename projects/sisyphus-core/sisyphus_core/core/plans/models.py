from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"


class RetrievalType(str, Enum):
    keywords = "keywords"
    prompt = "prompt"


class ExecutionStatus(BaseModel):
    started: bool
    completed: bool
    started_at: str | None = None
    completed_at: str | None = None


class WorkMode(BaseModel):
    parallel_requested: bool
    current_task_id: str | None = None


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


class DeterministicBashVerification(BaseModel):
    description: str
    reason_why_it_is_deterministic_and_reliable: str
    execute: str
    expected_stdout: str | None = None
    expected_stderr: str | None = None
    expected_exit_code: int = 0
    verified_at: str | None = None


class OrchestratorJudgeVerification(BaseModel):
    prompt: str
    verified_at: str | None = None
    verification_evidence: str | None = None


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
    deterministic_bash: list[DeterministicBashVerification] = []
    orchestrator_judge: list[OrchestratorJudgeVerification] = []

    @model_validator(mode="after")
    def validate_at_least_one(self) -> Self:
        if not self.bash and not self.llm_judge:
            raise ValueError("bash 또는 llm_judge 중 하나 이상 필수")
        return self


class UserRequest(BaseModel):
    original: str
    created_at: str
    additional: list[str] = []
    expected_outcome: str | None = None
    forbidden_outcome: str | None = None


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


class AcceptanceCriteriaItem(BaseModel):
    id: str
    condition: str
    verified_at: str | None = None
    verification_evidence: str | None = None


class Todo(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: TodoStatus
    children: list[Todo] | None = None
    references: list[ReferenceItem] = []
    verification_spec: list[VerificationItem] = []
    parallel: bool = False
    parallelable_and_safe_evidence: str | None = None
    acceptance_criteria: list[AcceptanceCriteriaItem] = []


class AcceptanceCriteriaChecklist(BaseModel):
    id: str
    title: str
    content: str
    checked_at: str | None = None
    checked_evidence: str | None = None


class AcceptanceCriteriaForVerificationAgent(BaseModel):
    id: str
    title: str
    accepted_at: str | None = None
    checklists: list[AcceptanceCriteriaChecklist] = []


class WorkPlan(BaseModel):
    id: str
    name: str
    depends_on: list[str] = []

    # === Required Overview Fields (v2.1 restoration) ===
    user_request: UserRequest
    objectives: Objectives
    background: Background
    required_background: RequiredBackground
    workflow: Workflow
    success_vision: SuccessVision
    final_verification: list[FinalVerificationItem]

    # === Core Fields ===
    todos: list[Todo]
    references: list[ReferenceItem] = []

    # === Status Fields ===
    execution: ExecutionStatus = Field(
        default_factory=lambda: ExecutionStatus(started=False, completed=False, started_at=None, completed_at=None)
    )
    work_mode: WorkMode = Field(default_factory=lambda: WorkMode(parallel_requested=False, current_task_id=None))
    current_work: str = ""
    current_work_ids: list[str] = []
    acceptance_criteria_for_verification_agent: list[AcceptanceCriteriaForVerificationAgent] = []
    fully_done_evidence: str | None = None


class Metadata(BaseModel):
    created_at: str
    updated_at: str | None = None


class RegistryPlanEntry(BaseModel):
    file: str
    plans: list[str]


class PlanRegistry(BaseModel):
    version: str
    plans: list[RegistryPlanEntry]


class PlanDocument(BaseModel):
    version: str
    metadata: Metadata
    work_plans: list[WorkPlan]
