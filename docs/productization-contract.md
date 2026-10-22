# Codex Flow — M12 Productization Contract

This contract freezes the M12 product-quality scope. M12 improves the local
release candidate without changing the deterministic scheduler or introducing
an external service requirement.

## Frozen boundaries

- Scheduler dependency, readiness, retry, failure, continuation, locking, and
  state-machine semantics remain unchanged.
- Codex integration remains behind `CodexAdapter`; M12 does not require live
  Codex execution and never treats UI text as execution evidence.
- The application remains local, single-user, and offline by default. There is
  no cloud service, multi-user mode, telemetry, background upload, or required
  network access.
- No new third-party runtime dependency, UI framework, system toolchain, or
  package download is introduced by M12.
- The application does not automatically scan the file system. User-selected
  files and explicit application-owned paths are the only data sources.
- Manual Desktop/UI checks remain a final handoff concern and are not silently
  converted into automated PASS claims.

## Workflow definitions

- Import and export operate on workflow definitions only: identity, name,
  tasks, edges, prompts, working directories, execution modes, retry policy,
  model/configuration fields, and other canonical definition fields.
- Run history, TaskRuns, Attempts, events, thread IDs, turn IDs, tokens, and
  diagnostics are never embedded in workflow definition exports.
- Export is explicit and deterministic. It writes only the user-requested
  destination and does not upload or discover additional files.
- Import validates the complete graph and canonical field contract before any
  durable write. Identity collision handling follows the dedicated M12 import
  policy task; import never silently overwrites an existing definition.
- Import/export round trips preserve definition semantics, including prompts,
  working directories, execution mode, continuation references, retry values,
  and graph edges.

## Diagnostics

- Diagnostics are explicit user actions, never background collection.
- Diagnostic output is a local, inspectable bundle containing only an
  allowlisted summary of application version, runtime status, paths, recent
  safe event metadata, and redacted error classes needed for support.
- Secrets and credentials are always excluded or redacted: bearer tokens,
  authorization headers, prompt content where policy marks it sensitive,
  environment values, private keys, and raw SDK payloads are not exported.
- Diagnostics do not perform network upload, telemetry, or automatic file
  discovery. The user chooses the destination and may inspect the result.

## Backup and restore boundary

- M12 provides an explicit export-only SQLite backup using the existing local
  database authority and online-backup semantics.
- Backup is written to a user-selected destination and never uploads data.
- There is no restore-in-place operation while the application is running.
  Restore is outside this M12 contract; backup creation must not alter live
  workflow/run state.

## History and event presentation

- Run history and event views remain read-only projections of durable local
  state.
- Pagination, filtering, search, and safe-copy behavior may improve access to
  large histories, but must not change event order, cursor semantics, or stored
  payloads.
- Copy/export actions use allowlisted fields and redact secrets before data
  leaves the view.

## Onboarding, accessibility, and performance

- First-run onboarding may offer canonical sample workflows and explicit
  creation/open actions; it must not create a run or invoke Codex implicitly.
- Empty, loading, error, and recovery states remain visible and actionable.
- Keyboard navigation, focus visibility, semantic labels, and accessible
  confirmation behavior are required for new and modified controls.
- Large DAG/history guards must keep rendering bounded and must not add
  background scanning, pagination side effects, or scheduler behavior.

## Acceptance rule

Every later M12 task must fit this contract. If a proposed change requires a
policy choice not encoded here, a new dependency, scheduler semantic change,
cloud/network behavior, or a live/manual claim before the final report, the
task is blocked rather than decided by implementation convenience.
