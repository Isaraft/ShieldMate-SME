import unicodedata
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from app.findings.schemas import DomainOption, FindingOut

Status = Literal["todo", "in_progress", "done"]


class EmptyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: StrictInt = Field(ge=1)
    status: Status | None = None
    owner_label: str | None = Field(default=None, max_length=80, strict=True)
    note: str | None = Field(default=None, max_length=2000, strict=True)

    @field_validator("owner_label", "note")
    @classmethod
    def safe_text(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Use an empty string to clear text")
        if any(unicodedata.category(c) in {"Cc", "Cs"} and c not in "\n\t" for c in value):
            raise ValueError("Control characters are not permitted")
        return value.strip()

    @model_validator(mode="after")
    def editable(self) -> "TaskPatch":
        changes = self.model_fields_set - {"version"}
        if not changes or ("status" in changes and self.status is None):
            raise ValueError("Supply status, owner label or note")
        return self


class TaskFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["all", "todo", "in_progress", "done"] = "all"
    severity: Literal["all", "high", "medium", "low", "info"] = "all"
    domain_id: UUID | None = None
    sort: Literal["updated", "oldest", "priority"] = "updated"
    offset: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=20, ge=1, le=50)


class TaskOut(BaseModel):
    id: str
    finding_id: str
    status: Status
    owner_label: str
    note: str
    created_at: int
    updated_at: int
    completed_at: int | None
    version: int
    history_truncated: bool
    reopened_at: int | None
    finding: FindingOut


class EventOut(BaseModel):
    id: str
    actor_id: str
    actor_label: str = "Workspace owner"
    version: int
    kind: str
    created_at: int
    changes: dict[str, dict[str, str]]


class TaskDetail(TaskOut):
    history: list[EventOut]


class TaskPage(BaseModel):
    items: list[TaskOut]
    total: int
    offset: int
    limit: int
    domains: list[DomainOption]
