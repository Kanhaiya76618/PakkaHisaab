"""Cross-file contract checks for the Milestone 2.5 integration audit."""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import fields
from pathlib import Path

from events import AgentLogEvent
from intake.types import ExtractedEntryDraft


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
MIGRATIONS = ROOT / "supabase" / "migrations"
IGNORED_PARTS = {".venv", "node_modules", ".next", "__pycache__"}


def _table_columns(table: str) -> set[str]:
    sql = "\n".join(path.read_text(encoding="utf-8") for path in sorted(MIGRATIONS.glob("*.sql")))
    match = re.search(rf"create table public\.{table} \((.*?)\n\);", sql, flags=re.DOTALL)
    assert match, f"missing {table} table in migration"
    columns = {
        line.strip().split()[0]
        for line in match.group(1).splitlines()
        if line.strip() and not line.lstrip().startswith(("constraint", "primary", "foreign"))
    }
    columns.update(
        re.findall(rf"alter table public\.{table}\s+add column(?: if not exists)?\s+([a-z_]+)", sql, flags=re.IGNORECASE)
    )
    return columns


def _project_sources() -> list[Path]:
    paths = [*BACKEND.rglob("*.py"), *FRONTEND.rglob("*.ts"), *FRONTEND.rglob("*.tsx")]
    return [path for path in paths if not any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)]


def _documented_env_names() -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"^([A-Z][A-Z0-9_]+)=", (ROOT / ".env.example").read_text(encoding="utf-8"), re.MULTILINE)
    }


def _read_env_names() -> set[str]:
    names: set[str] = set()
    for source in _project_sources():
        text = source.read_text(encoding="utf-8")
        names.update(re.findall(r"(?:os\.getenv|os\.environ\.get|process\.env)\(?(?:\[)?[\"']([A-Z][A-Z0-9_]+)[\"']", text))
        names.update(re.findall(r"process\.env\.([A-Z][A-Z0-9_]+)", text))
    return names


def test_backend_entrypoint_modules_import_cleanly() -> None:
    for module_name in ("config", "db", "auth", "events", "model_router", "intake.csv_parser", "agents.intake_agent", "main"):
        assert importlib.import_module(module_name)


def test_extraction_draft_fields_fit_the_postgres_table() -> None:
    columns = _table_columns("extracted_entries")
    persisted = {field.name for field in fields(ExtractedEntryDraft)}
    assert persisted <= columns


def test_profile_schema_matches_supabase_patch_contract() -> None:
    sql = "\n".join(path.read_text(encoding="utf-8") for path in sorted(MIGRATIONS.glob("*.sql")))
    assert "display_name text" in sql
    assert "preferred_lang text not null default 'hi'" in sql
    assert "check (preferred_lang in ('hi', 'en'))" in sql
    assert "insert into public.profiles (id, display_name)" in sql


def test_router_fixture_shape_matches_intake_contract() -> None:
    fixture_dir = ROOT / "sample_data" / "fixtures"
    expected = {"entry_type", "party_name", "amount_rupees", "entry_date", "description", "row_ref", "confidence"}
    for path in (fixture_dir / "vision_khaata.json", fixture_dir / "vision_invoice.json"):
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload["entries"], list) and payload["entries"]
        assert expected <= set(payload["entries"][0])


def test_placeholder_fixtures_match_generated_ground_truth() -> None:
    import json

    fixture_dir = ROOT / "sample_data" / "fixtures"
    khaata = json.loads((fixture_dir / "vision_khaata.json").read_text(encoding="utf-8"))["entries"]
    invoice = json.loads((fixture_dir / "vision_invoice.json").read_text(encoding="utf-8"))["entries"]
    financial_rows = [entry for entry in khaata if entry["entry_type"] != "note"]

    assert len(financial_rows) == 8
    assert sum(entry["amount_rupees"] for entry in financial_rows) == 18_730
    assert khaata[-1] == {
        "entry_type": "note",
        "party_name": None,
        "amount_rupees": 18_930,
        "entry_date": "2026-07-12",
        "description": "written_total",
        "row_ref": "page 1, written total",
        "confidence": 1.0,
    }
    # `vision_invoice.json` is now a LIVE RECORDING from a real vision call against a
    # photographed invoice, not a hand-written placeholder. Its prose is therefore the
    # model's own and will legitimately differ between recordings, so this asserts every
    # field that ground truth can actually adjudicate — and asserts them exactly — rather
    # than pinning a sentence. Party is compared case-insensitively because the invoice is
    # printed in upper case and the engine casefolds party names before matching.
    assert len(invoice) == 1
    recorded = invoice[0]
    assert recorded["entry_type"] == "purchase", "these are the buyer's books"
    assert recorded["party_name"].casefold() == "mehta kirana shop"
    assert recorded["amount_rupees"] == 4800
    assert recorded["entry_date"] == "2026-07-12"
    assert recorded["confidence"] >= 0.9
    assert recorded["row_ref"]
    # Every line item and extension on the paper must survive into the description.
    for fragment in ("231", "ATTA", "SUNFLOWER OIL", "SUGAR", "2,600", "1,900", "300", "4,800"):
        assert fragment in recorded["description"], fragment


def test_websocket_event_contract_matches_frontend_terminal() -> None:
    assert set(AgentLogEvent.model_fields) == {"agent", "level", "message_en", "message_hi", "detail"}
    terminal = (FRONTEND / "components" / "AgentTerminal.tsx").read_text(encoding="utf-8")
    for field in AgentLogEvent.model_fields:
        assert f"event.{field}" in terminal or field in re.search(r"type AgentLog = (.*)", terminal).group(1)


def test_demo_route_contract_has_a_frontend_zod_schema() -> None:
    api_file = FRONTEND / "lib" / "api.ts"
    assert api_file.is_file(), "frontend API response validation is required at the route seam"
    api = api_file.read_text(encoding="utf-8")
    assert "z.object" in api
    for field in ("store_id", "is_public", "is_demo"):
        assert field in api


def test_all_runtime_environment_reads_are_documented() -> None:
    assert _read_env_names() <= _documented_env_names()


def test_design_tokens_and_devanagari_fallbacks_are_present() -> None:
    for path in (FRONTEND / "components").glob("*.tsx"):
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", path.read_text(encoding="utf-8")), path
    css = (FRONTEND / "app" / "globals.css").read_text(encoding="utf-8")
    assert '"Noto Sans Devanagari"' in css
    assert '"JetBrains Mono", "Noto Sans Devanagari", monospace' in css


def test_backend_local_import_graph_has_no_cycles() -> None:
    modules = {
        path.relative_to(BACKEND).with_suffix("").as_posix().replace("/", ".")
        for path in BACKEND.rglob("*.py")
        if "tests" not in path.parts and not any(part in IGNORED_PARTS for part in path.relative_to(BACKEND).parts)
    }
    graph: dict[str, set[str]] = {module: set() for module in modules}
    for module in modules:
        path = BACKEND / (module.replace(".", "/") + ".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in modules:
                graph[module].add(node.module)
            if isinstance(node, ast.Import):
                graph[module].update(alias.name for alias in node.names if alias.name in modules)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module: str) -> None:
        assert module not in visiting, f"circular backend import involving {module}"
        if module in visited:
            return
        visiting.add(module)
        for dependency in graph[module]:
            visit(dependency)
        visiting.remove(module)
        visited.add(module)

    for module in graph:
        visit(module)
