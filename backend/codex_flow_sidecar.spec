from pathlib import Path

from PyInstaller.utils.hooks import collect_all


BACKEND_ROOT = Path(SPECPATH).resolve()
SOURCE_ROOT = BACKEND_ROOT / "src"
MIGRATION_ROOT = SOURCE_ROOT / "codex_flow" / "storage" / "migrations"

codex_datas, codex_binaries, codex_hiddenimports = collect_all("openai_codex")
migration_datas = [
    (str(path), "codex_flow/storage/migrations") for path in MIGRATION_ROOT.glob("*.sql")
]

analysis = Analysis(
    [str(SOURCE_ROOT / "codex_flow" / "server.py")],
    pathex=[str(SOURCE_ROOT)],
    binaries=codex_binaries,
    datas=codex_datas + migration_datas,
    hiddenimports=codex_hiddenimports
    + [
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(analysis.pure)
executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="codex-flow-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    name="codex-flow-server",
)
