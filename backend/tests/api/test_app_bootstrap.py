from fastapi.openapi.utils import get_openapi

from codex_flow.api import create_app


def test_api_import_and_app_construction_have_no_runtime_side_effects() -> None:
    app = create_app()

    assert app.title == "Codex Flow Local API"
    assert get_openapi(title=app.title, version=app.version, routes=app.routes)["openapi"]
