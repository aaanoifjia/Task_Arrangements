# M11-BUILD-034 — Release Executable Local Smoke

The release smoke checks remain local and do not launch live Codex or make any
manual UI claim.

## Automated checks

```powershell
\.venv\Scripts\python.exe -m pytest backend/tests/packaging/test_packaged_sidecar_contract.py --basetemp backend/.pytest-tmp/m11-build-034
```

The test module covers:

- release executable presence and Windows PE `MZ`/`PE\0\0` headers without
  opening a GUI;
- real packaged sidecar readiness JSON;
- loopback `/healthz`;
- authenticated `/api/system/status`;
- clean sidecar process termination.

No live Codex turn, credentials, installer launch, or manual Desktop observation
is part of this smoke evidence.

## Recorded acceptance

After the bounded `M11-BUILD-034-R1` staging repair, the local NSIS build and
the focused contract suite passed:

```text
backend/tests/packaging/test_packaged_sidecar_contract.py: 2 passed
ruff check backend/tests/packaging/test_packaged_sidecar_contract.py: passed
canonical staged migration: binaries/_internal/codex_flow/storage/migrations/0003_query_indexes.sql: present
nested binaries/_internal/_internal tree: absent
```

Current local artifact evidence:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9092096 | `BF51691978E5011724410B215E2C622C0F6ECFF7705820713E38B003113F1FAE` |
| `desktop/src-tauri/binaries/codex-flow-server-x86_64-pc-windows-msvc.exe` | 5717136 | `8C8C82891E1A613303134B43081DFEF1C0B53347A92ADBA6223EB8FCBD562029` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7610573 | `83E66B92153E1C227842ACFFDA39F8CCF13CB831B00B7729620FDC9F4F47E7EB` |

## Recorded acceptance

After the bounded `M11-BUILD-034-R1` staging repair, the local NSIS build and
the focused contract suite passed:

```text
backend/tests/packaging/test_packaged_sidecar_contract.py: 2 passed
ruff check backend/tests/packaging/test_packaged_sidecar_contract.py: passed
canonical staged migration: binaries/_internal/codex_flow/storage/migrations/0003_query_indexes.sql: present
nested binaries/_internal/_internal tree: absent
```

Current local artifact evidence:

| Artifact | Size (bytes) | SHA256 |
| --- | ---: | --- |
| `desktop/src-tauri/target/release/codex-flow-desktop.exe` | 9092096 | `BF51691978E5011724410B215E2C622C0F6ECFF7705820713E38B003113F1FAE` |
| `desktop/src-tauri/binaries/codex-flow-server-x86_64-pc-windows-msvc.exe` | 5717136 | `8C8C82891E1A613303134B43081DFEF1C0B53347A92ADBA6223EB8FCBD562029` |
| `desktop/src-tauri/target/release/bundle/nsis/Codex Flow_0.1.0_x64-setup.exe` | 7610573 | `83E66B92153E1C227842ACFFDA39F8CCF13CB831B00B7729620FDC9F4F47E7EB` |
