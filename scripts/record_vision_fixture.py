"""Record a vision fixture from a real model call against a real document.

This is the escape hatch out of placeholder fixtures. Point it at a committed image, and it
routes the matching task through `model_router` with `MOCK_MODE=false`, then writes the
model's **verbatim** output to the fixture with provenance recorded — provider, deployment,
token counts, latency, and the date.

    python scripts/record_vision_fixture.py --task vision_invoice \\
        --image sample_data/mehta_inv_231.jpg

It never edits the model's output to match expectations. If a recording disagrees with
`sample_data/GROUND_TRUTH.md`, that disagreement is the measurement — keep the recording and
fix the prompt or the ground truth, not the fixture.

Credentials come from `backend/.env` (Azure OpenAI or direct OpenAI). Nothing is printed
that could leak a key.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

PROMPT_BY_TASK = {
    "vision_invoice": "INVOICE_SYSTEM_PROMPT",
    "vision_khaata": "KHAATA_SYSTEM_PROMPT",
}


def load_env(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


async def record(task: str, image: Path, fixture: Path) -> None:
    import agents.intake_agent as intake
    from model_router import FIXTURE_BY_TASK, MODEL_CALLS, resolve_chat_provider, route

    prompt = getattr(intake, PROMPT_BY_TASK[task])
    encoded = base64.b64encode(image.read_bytes()).decode()
    print(f"task={task} image={image.name} provider={resolve_chat_provider()}")

    result = await route(
        task,
        {
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Extract {image.name}."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                    ],
                },
            ]
        },
        mock_mode=False,
    )

    call = MODEL_CALLS[-1]
    payload = {
        "_provenance": (
            f"LIVE RECORDING — not a placeholder. Captured by scripts/record_vision_fixture.py "
            f"against {image.name}. Served by {call.provider} deployment/model {call.model}, "
            f"{call.input_tokens} prompt + {call.output_tokens} completion tokens, "
            f"{call.latency_ms} ms. Verbatim model output, unedited."
        ),
        "_source_document": image.name,
        **result,
    }
    target = fixture or (ROOT / "sample_data" / "fixtures" / FIXTURE_BY_TASK[task])
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target if target.is_absolute() and ROOT not in target.parents else target.relative_to(ROOT)}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\nNow diff every field against sample_data/GROUND_TRUTH.md before committing.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(PROMPT_BY_TASK), required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=None, help="override the output path")
    parser.add_argument("--env", type=Path, default=ROOT / "backend" / ".env")
    args = parser.parse_args()

    load_env(args.env)
    image = args.image if args.image.is_absolute() else ROOT / args.image
    if not image.is_file():
        raise SystemExit(f"image not found: {image}")
    asyncio.run(record(args.task, image, args.fixture))


if __name__ == "__main__":
    main()
