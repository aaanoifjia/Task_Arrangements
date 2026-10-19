"""Workflow application service with domain validation and error translation."""

from codex_flow.domain.models import WorkflowDefinition
from codex_flow.storage.repositories import StorageRepositories


class WorkflowServiceError(ValueError):
    """Base error for deterministic workflow service failures."""


class WorkflowNotFoundError(WorkflowServiceError):
    """The requested workflow does not exist."""


class WorkflowIdMismatchError(WorkflowServiceError):
    """The path and body workflow IDs do not match."""


class WorkflowApplicationService:
    def __init__(self, repository: StorageRepositories) -> None:
        self._repository = repository

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        validated = WorkflowDefinition.model_validate(workflow.model_dump())
        self._repository.save_workflow_definition(validated)
        return validated

    def update(self, workflow_id: str, workflow: WorkflowDefinition) -> WorkflowDefinition:
        if workflow_id != workflow.id:
            raise WorkflowIdMismatchError("workflow path and body IDs must match")
        if self._repository.load_workflow(workflow_id) is None:
            raise WorkflowNotFoundError(f"workflow not found: {workflow_id}")
        return self.save(workflow)

    def list(self) -> list[WorkflowDefinition]:
        return [
            workflow
            for row in self._repository.list_workflows()
            if (workflow := WorkflowDefinition.model_validate_json(row["definition_json"])) is not None
        ]

    def get(self, workflow_id: str) -> WorkflowDefinition:
        workflow = self._repository.load_workflow(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(f"workflow not found: {workflow_id}")
        return workflow
