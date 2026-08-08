#!/usr/bin/env python3
"""Surface the effective model and configured reasoning for each subagent."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path


UNEXPOSED_REASONING = "runtime-selected (not exposed by SubagentStart)"


def _role_config(agent_type: str) -> dict[str, object]:
    role_path = Path(__file__).resolve().parents[1] / "agents" / f"{agent_type}.toml"
    try:
        return tomllib.loads(role_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def build_message(payload: dict[str, object]) -> str:
    agent_type = str(payload.get("agent_type") or "unknown")
    config = _role_config(agent_type)
    model = str(payload.get("model") or config.get("model") or "runtime-selected")
    configured_effort = config.get("model_reasoning_effort")
    if configured_effort:
        reasoning = str(configured_effort)
    elif agent_type == "default" and not config.get("model"):
        reasoning = "inherited from parent"
    else:
        reasoning = UNEXPOSED_REASONING
    return (
        f"Subagent started | role: {agent_type} | model: {model} | "
        f"reasoning: {reasoning}"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as error:
        print(json.dumps({"systemMessage": f"Subagent disclosure unavailable: {error}"}))
        return 0
    if not isinstance(payload, dict):
        payload = {}
    print(json.dumps({"systemMessage": build_message(payload)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
