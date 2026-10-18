# Codex Flow

Codex Flow is a local, deterministic DAG scheduler for orchestrating Codex tasks with explicit prompts and dependencies.

The project is currently in the early headless-core phase.

## Backend setup

Requirements:

- Windows
- Python 3.11+

Create the virtual environment:

```powershell
py -3.11 -m venv .venv
```

Install the backend in editable mode:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
```

Verify the package:

```powershell
.\.venv\Scripts\python.exe -c "import codex_flow; print(codex_flow.__version__)"
```
