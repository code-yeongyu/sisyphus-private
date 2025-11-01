from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, model_validator


class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"


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
    type: str
    description: str
    command: str | None = None
    expected_output: str | None = None


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


class Metadata(BaseModel):
    created_at: str
    updated_at: str | None = None


class PlanDocument(BaseModel):
    version: str
    metadata: Metadata
    work_plans: list[WorkPlan]
