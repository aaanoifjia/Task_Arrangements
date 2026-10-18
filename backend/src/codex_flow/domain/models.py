from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class ExecutionMode(StrEnum):
    NEW_THREAD = "NEW_THREAD"
    CONTINUE_THREAD = "CONTINUE_THREAD"


class SandboxMode(StrEnum):
    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"
    FULL_ACCESS = "full_access"


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=1, ge=1)


class TaskDefinition(BaseModel):
    id: str
    name: str
    prompt: str
    cwd: str
    dependencies: list[str] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.NEW_THREAD
    continue_from_task_id: str | None = None
    model: str | None = None
    reasoning_effort: str | None = None
    sandbox: SandboxMode = SandboxMode.WORKSPACE_WRITE
    approval_mode: str | None = None
    timeout_seconds: int | None = None
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)

    @field_validator("id", "name", "prompt", "cwd")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty or whitespace")
        return value

    @model_validator(mode="after")
    def validate_thread_mode(self) -> "TaskDefinition":
        if self.execution_mode is ExecutionMode.CONTINUE_THREAD and self.continue_from_task_id is None:
            raise ValueError("continue_from_task_id is required")
        if self.execution_mode is ExecutionMode.NEW_THREAD and self.continue_from_task_id is not None:
            raise ValueError("continue_from_task_id must be None")
        return self


class Edge(BaseModel):
    source_task_id: str
    target_task_id: str


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str | None = None
    tasks: list[TaskDefinition]
    edges: list[Edge]

