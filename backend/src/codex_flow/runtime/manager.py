"""Tracked non-blocking execution of durable workflow runs."""

import asyncio

from codex_flow.application.control_contract import (
    ControlAction,
    ControlCommand,
    ControlResult,
    accepted_result,
    rejected_result,
)
from codex_flow.codex_adapter.interface import CodexAdapter
from codex_flow.codex_adapter.models import CodexTurnRef
from codex_flow.domain.models import WorkflowDefinition
from codex_flow.domain.status import TaskStatus, is_terminal
from codex_flow.runtime.runner import DurableRunner
from codex_flow.scheduler.state_machine import TransitionTrigger, transition
from codex_flow.storage.repositories import StorageRepositories


class RuntimeManager:
    def __init__(self, repository: StorageRepositories, adapter: CodexAdapter) -> None:
        self._repository = repository
        self._adapter = adapter
        self._runner = DurableRunner(repository, adapter)
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._accepting = True

    async def start(self, workflow: WorkflowDefinition) -> str:
        if not self._accepting:
            raise RuntimeError("runtime manager is shutting down")
        run_id = self._runner.prepare_run(workflow)
        self._workflows[run_id] = workflow
        task = asyncio.create_task(self._runner.execute_run(run_id, workflow))
        self._tasks[run_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run_id, None))
        return run_id

    async def pause(self, run_id: str) -> ControlResult:
        """Durably pause an active run without interrupting its current turn."""
        command = ControlCommand(run_id=run_id, action=ControlAction.PAUSE)
        row = self._repository.get_workflow_run(run_id)
        if row is None:
            return rejected_result(command, error_code="RUN_NOT_FOUND", message="run not found")
        status = TaskStatus(str(row["status"]))
        if is_terminal(status):
            result = rejected_result(
                command,
                error_code="RUN_NOT_ACTIVE",
                message=f"run is already terminal: {status.value}",
            )
            self._repository.append_manual_action_audit(result)
            return result
        if self._repository.get_workflow_run_paused(run_id):
            result = rejected_result(
                command,
                error_code="ALREADY_PAUSED",
                message="run is already paused",
            )
            self._repository.append_manual_action_audit(result)
            return result
        self._repository.set_workflow_run_paused(run_id, True)
        result = accepted_result(command)
        self._repository.append_manual_action_audit(result)
        return result

    async def resume(self, run_id: str) -> ControlResult:
        """Clear pause and schedule exactly one unfinished run continuation."""
        command = ControlCommand(run_id=run_id, action=ControlAction.RESUME)
        row = self._repository.get_workflow_run(run_id)
        if row is None:
            return rejected_result(command, error_code="RUN_NOT_FOUND", message="run not found")
        status = TaskStatus(str(row["status"]))
        if is_terminal(status):
            result = rejected_result(
                command,
                error_code="RUN_NOT_ACTIVE",
                message=f"run is already terminal: {status.value}",
            )
            self._repository.append_manual_action_audit(result)
            return result
        if not self._repository.get_workflow_run_paused(run_id):
            result = rejected_result(
                command,
                error_code="NOT_PAUSED",
                message="run is not paused",
            )
            self._repository.append_manual_action_audit(result)
            return result

        self._repository.set_workflow_run_paused(run_id, False)
        result = accepted_result(command)
        self._repository.append_manual_action_audit(result)
        task = self._tasks.get(run_id)
        if task is not None and task.done():
            self._tasks.pop(run_id, None)
        if run_id not in self._tasks:
            workflow = self._workflows.get(run_id)
            if workflow is None:
                raise ValueError(f"workflow definition not available for run: {run_id}")
            task = asyncio.create_task(self._runner.execute_run(run_id, workflow))
            self._tasks[run_id] = task
            task.add_done_callback(lambda _: self._tasks.pop(run_id, None))
        return result

    async def retry(self, run_id: str, task_run_id: str) -> ControlResult:
        """Reset a retryable task and reopen one durable run execution."""
        command = ControlCommand(run_id=run_id, action=ControlAction.RETRY, task_id=task_run_id)
        row = self._repository.get_workflow_run(run_id)
        task_row = self._repository.get_task_run(task_run_id)
        if row is None or task_row is None or str(task_row["workflow_run_id"]) != run_id:
            return rejected_result(command, error_code="TASK_NOT_FOUND", message="task run not found")
        status = TaskStatus(str(row["status"]))
        if is_terminal(status) and status not in {
            TaskStatus.FAILED,
            TaskStatus.INTERRUPTED,
        }:
            result = rejected_result(
                command,
                error_code="RUN_NOT_RETRYABLE",
                message=f"run is not retryable: {status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        previous_status = TaskStatus(str(task_row["status"]))
        if previous_status not in {
            TaskStatus.FAILED,
            TaskStatus.INTERRUPTED,
            TaskStatus.NEEDS_ATTENTION,
        }:
            result = rejected_result(
                command,
                error_code="TASK_NOT_RETRYABLE",
                message=f"task is not retryable: {previous_status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result

        self._repository.reset_task_for_retry(task_run_id)
        self._repository.update_workflow_run_state(run_id, TaskStatus.RUNNING.value)
        result = accepted_result(command, previous_status=previous_status)
        self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
        task = self._tasks.get(run_id)
        if task is not None and task.done():
            self._tasks.pop(run_id, None)
        if run_id not in self._tasks:
            workflow = self._workflows.get(run_id)
            if workflow is None:
                raise ValueError(f"workflow definition not available for run: {run_id}")
            task = asyncio.create_task(self._runner.execute_run(run_id, workflow))
            self._tasks[run_id] = task
            task.add_done_callback(lambda _: self._tasks.pop(run_id, None))
        return result

    async def cancel(self, run_id: str, task_run_id: str) -> ControlResult:
        """Cancel a queued task through the canonical user-action transition."""
        command = ControlCommand(run_id=run_id, action=ControlAction.CANCEL, task_id=task_run_id)
        run = self._repository.get_workflow_run(run_id)
        task_row = self._repository.get_task_run(task_run_id)
        if run is None or task_row is None or str(task_row["workflow_run_id"]) != run_id:
            return rejected_result(command, error_code="TASK_NOT_FOUND", message="task run not found")
        run_status = TaskStatus(str(run["status"]))
        if is_terminal(run_status):
            result = rejected_result(
                command,
                error_code="RUN_NOT_ACTIVE",
                message=f"run is already terminal: {run_status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        previous_status = TaskStatus(str(task_row["status"]))
        if previous_status in {TaskStatus.STARTING, TaskStatus.RUNNING}:
            return await self._cancel_running(run_id, task_run_id, command, previous_status)
        if previous_status not in {TaskStatus.PENDING, TaskStatus.BLOCKED, TaskStatus.READY}:
            result = rejected_result(
                command,
                error_code="TASK_NOT_QUEUED",
                message=f"task is not queued: {previous_status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        transition(previous_status, TaskStatus.CANCELLED, TransitionTrigger.USER_ACTION)
        if not self._repository.compare_and_update_task_run_state(
            task_run_id, previous_status.value, TaskStatus.CANCELLED.value
        ):
            result = rejected_result(
                command, error_code="STALE_STATE", message="task state changed before cancellation"
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        result = accepted_result(command, previous_status=previous_status)
        self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
        return result

    async def skip(self, run_id: str, task_run_id: str) -> ControlResult:
        """Skip only states permitted by the canonical user-action transition."""
        command = ControlCommand(run_id=run_id, action=ControlAction.SKIP, task_id=task_run_id)
        run = self._repository.get_workflow_run(run_id)
        task_row = self._repository.get_task_run(task_run_id)
        if run is None or task_row is None or str(task_row["workflow_run_id"]) != run_id:
            return rejected_result(command, error_code="TASK_NOT_FOUND", message="task run not found")
        run_status = TaskStatus(str(run["status"]))
        if is_terminal(run_status):
            result = rejected_result(
                command,
                error_code="RUN_NOT_ACTIVE",
                message=f"run is already terminal: {run_status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        previous_status = TaskStatus(str(task_row["status"]))
        if previous_status not in {TaskStatus.BLOCKED, TaskStatus.READY}:
            result = rejected_result(
                command,
                error_code="TASK_NOT_SKIPPABLE",
                message=f"task cannot be skipped from {previous_status.value}",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        transition(previous_status, TaskStatus.SKIPPED, TransitionTrigger.USER_ACTION)
        if not self._repository.compare_and_update_task_run_state(
            task_run_id, previous_status.value, TaskStatus.SKIPPED.value
        ):
            result = rejected_result(
                command, error_code="STALE_STATE", message="task state changed before skip"
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        result = accepted_result(command, previous_status=previous_status)
        self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
        return result

    async def _cancel_running(
        self,
        run_id: str,
        task_run_id: str,
        command: ControlCommand,
        previous_status: TaskStatus,
    ) -> ControlResult:
        turn = self._runner.active_turn(task_run_id)
        if turn is None:
            result = rejected_result(
                command,
                error_code="EXTERNAL_STATE_UNKNOWN",
                message="running task has no active turn",
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        try:
            await self._adapter.interrupt_turn(turn)
        except Exception as error:  # noqa: BLE001 - adapter failures must fail closed
            result = rejected_result(
                command, error_code="INTERRUPT_FAILED", message=str(error) or "interrupt failed"
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        if not self._repository.compare_and_update_task_run_state(
            task_run_id,
            previous_status.value,
            TaskStatus.CANCELLED.value,
            turn.thread_id,
            turn.turn_id,
        ):
            result = rejected_result(
                command, error_code="STALE_STATE", message="task state changed before cancellation"
            )
            self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
            return result
        attempts = self._repository.load_attempts(task_run_id)
        if attempts:
            self._repository.update_attempt_state(str(attempts[-1]["id"]), TaskStatus.CANCELLED.value)
        result = accepted_result(command, previous_status=previous_status)
        self._repository.append_manual_action_audit(result, task_run_id=task_run_id)
        return result

    async def wait(self, run_id: str) -> None:
        task = self._tasks.get(run_id)
        if task is None:
            row = self._repository.get_workflow_run(run_id)
            if row is None:
                raise KeyError(f"run not found: {run_id}")
            return
        await task

    @property
    def active_count(self) -> int:
        return len(self._tasks)

    def active_turn(self, task_run_id: str) -> CodexTurnRef | None:
        """Expose the runner's process-local active turn for explicit controls."""
        return self._runner.active_turn(task_run_id)

    @property
    def active_turns(self) -> dict[str, CodexTurnRef]:
        return self._runner.active_turns

    async def shutdown(self) -> None:
        self._accepting = False
        tasks = tuple(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
