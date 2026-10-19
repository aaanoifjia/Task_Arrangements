"""SDK-independent data exchanged through the Codex adapter boundary."""

from enum import StrEnum

from pydantic import BaseModel, Field

from codex_flow.domain.models import SandboxMode


class EventType(StrEnum):
    THREAD_CREATED = "THREAD_CREATED"
    TURN_STARTED = "TURN_STARTED"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TURN_COMPLETED = "TURN_COMPLETED"
    TURN_FAILED = "TURN_FAILED"
    TURN_INTERRUPTED = "TURN_INTERRUPTED"
    ATTENTION_REQUIRED = "ATTENTION_REQUIRED"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"


class CodexThreadRef(BaseModel):
    thread_id: str


class CodexTurnRef(BaseModel):
    thread_id: str
    turn_id: str


class CodexEvent(BaseModel):
    event_type: EventType
    thread_id: str
    turn_id: str | None = None
    message: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class CodexTurnOutcome(BaseModel):
    thread_id: str
    turn_id: str
    terminal_event: EventType
    error_message: str | None = None


class CodexThreadSnapshot(BaseModel):
    thread: CodexThreadRef
    name: str | None = None


class CodexExecutionConfig(BaseModel):
    cwd: str
    sandbox: SandboxMode = SandboxMode.WORKSPACE_WRITE
    model: str | None = None
    reasoning_effort: str | None = None
    approval_mode: str | None = None
