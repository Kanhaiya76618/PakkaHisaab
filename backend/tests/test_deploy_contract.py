"""Deploy contract — the checks that would have caught the Railway build failure.

Two failures happened on the first Railway attempt, and both are structural rather than
accidental, so they belong in the suite:

1. Railpack builds from the repository root and found no Python manifest there, so it could
   not detect a language and exited.
2. `main.py` resolves `ROOT = parents[1]` and reads `ROOT/sample_data` inside its **startup**
   hook. Building with Railway's Root Directory set to `backend` excludes `sample_data/` from
   the build context, so the service would have built and then crashed on boot. The original
   DEPLOY.md instructed exactly that.

Together these pin the layout the deploy actually needs: build from the root, start from
`backend/`.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# What the FastAPI app needs to import and serve a request.
RUNTIME_DEPENDENCIES = ("fastapi", "uvicorn", "httpx", "pyjwt", "python-multipart", "reportlab")

# Files the app reads at runtime, relative to the repository root. Every one of these is
# outside `backend/`, which is the whole reason the build context must be the root.
RUNTIME_DATA = (
    "sample_data/july_upi.csv",
    "sample_data/fixtures/vision_khaata.json",
    "sample_data/fixtures/risk_history.json",
    "sample_data/mehta_inv_231.jpg",
)


def test_a_python_manifest_exists_where_the_builder_looks() -> None:
    """Railpack detects the language from the build context root. Without a manifest there
    it exits before installing anything — which is exactly what happened."""
    assert (ROOT / "requirements.txt").is_file(), "root requirements.txt is what railpack detects"


def test_root_requirements_cover_every_runtime_dependency() -> None:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    # The root manifest may include the backend's list rather than duplicating it.
    if "-r " in text:
        for line in text.splitlines():
            if line.strip().startswith("-r "):
                included = ROOT / line.split("-r", 1)[1].strip()
                assert included.is_file(), f"included manifest missing: {included}"
                text += included.read_text(encoding="utf-8").lower()
    for package in RUNTIME_DEPENDENCIES:
        assert package in text, f"{package} is imported at runtime but absent from requirements"


def test_runtime_data_lives_outside_backend_so_the_root_must_be_the_build_context() -> None:
    for relative in RUNTIME_DATA:
        assert (ROOT / relative).is_file(), relative
        assert not relative.startswith("backend/"), (
            f"{relative} is outside backend/, so a backend-only build context would omit it"
        )


def test_railway_config_starts_the_app_from_the_backend_directory() -> None:
    """`uvicorn main:app` only resolves with `backend/` as the working directory, while the
    build context has to be the root. The start command is what reconciles those."""
    config_path = ROOT / "railway.toml"
    assert config_path.is_file(), "railway.toml must sit at the build context root"
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))

    start = config["deploy"]["startCommand"]
    assert "backend" in start, "the app must be started from backend/ for `main` to import"
    assert "main:app" in start
    assert "$PORT" in start, "Railway assigns the port at runtime"
    assert config["deploy"]["healthcheckPath"] == "/api/health"


def test_no_stale_backend_railway_config_invites_the_broken_layout() -> None:
    """A `backend/railway.toml` would only be read if Root Directory were set to `backend`,
    which is the layout that loses `sample_data/`. Keeping one would re-plant the trap."""
    assert not (ROOT / "backend" / "railway.toml").exists()


def test_python_version_is_declared_where_the_builder_reads_it() -> None:
    """Railpack reads `.python-version`; `runtime.txt` is a Heroku convention it ignores."""
    version_file = ROOT / ".python-version"
    assert version_file.is_file()
    assert version_file.read_text(encoding="utf-8").strip().startswith("3.")
