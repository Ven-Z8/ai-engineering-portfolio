#!/usr/bin/env python3
"""Merge Claude Code env from claude-code.provider.json into .claude/settings.local.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVIDER_FILE = ROOT / "claude-code.provider.json"
SETTINGS_FILE = ROOT / ".claude" / "settings.local.json"
OPENROUTER_KEY_FILE = ROOT / ".openrouter_api_key"
OPENROUTER_ENV_FILE = ROOT / "openrouter.env"
ANTHROPIC_KEY_FILE = ROOT / ".anthropic_api_key"
ANTHROPIC_ENV_FILE = ROOT / "anthropic.env"


def _read_secret_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _read_env_assignment(path: Path, name: str) -> str | None:
    """Read KEY=value from a simple dotenv-style file (one assignment per line)."""
    if not path.is_file():
        return None
    prefix = f"{name}="
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(prefix):
            val = line[len(prefix) :].strip().strip('"').strip("'")
            return val or None
    return None


def _openrouter_key() -> str | None:
    return (
        os.environ.get("OPENROUTER_API_KEY")
        or _read_secret_file(OPENROUTER_KEY_FILE)
        or _read_env_assignment(OPENROUTER_ENV_FILE, "OPENROUTER_API_KEY")
        or _read_env_assignment(ROOT / ".env", "OPENROUTER_API_KEY")
    )


def _anthropic_key() -> str | None:
    return (
        os.environ.get("ANTHROPIC_API_KEY")
        or _read_secret_file(ANTHROPIC_KEY_FILE)
        or _read_env_assignment(ANTHROPIC_ENV_FILE, "ANTHROPIC_API_KEY")
        or _read_env_assignment(ROOT / ".env", "ANTHROPIC_API_KEY")
    )


def _missing_openrouter_help() -> None:
    root = str(ROOT)
    print(
        "Missing OpenRouter API key. Use one of:\n"
        f"  1. export OPENROUTER_API_KEY='sk-or-...'\n"
        f"  2. echo 'sk-or-...' > {root}/.openrouter_api_key   (one line, no quotes in file)\n"
        f"  3. Create {root}/openrouter.env containing:\n"
        f"       OPENROUTER_API_KEY=sk-or-...\n"
        f"  4. Add OPENROUTER_API_KEY=... to {root}/.env if you use that file\n",
        file=sys.stderr,
    )


def _missing_anthropic_help() -> None:
    root = str(ROOT)
    print(
        "Missing Anthropic API key. Use one of:\n"
        f"  1. export ANTHROPIC_API_KEY='sk-ant-...'\n"
        f"  2. echo 'sk-ant-...' > {root}/.anthropic_api_key\n"
        f"  3. Create {root}/anthropic.env with ANTHROPIC_API_KEY=sk-ant-...\n",
        file=sys.stderr,
    )


def _build_env(active: str, data: dict) -> dict[str, str]:
    if active == "openrouter":
        key = _openrouter_key()
        if not key:
            _missing_openrouter_help()
            sys.exit(1)
        env: dict[str, str] = {
            "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
            "ANTHROPIC_AUTH_TOKEN": key,
            "ANTHROPIC_API_KEY": "",
        }
        models = data.get("models_openrouter") or {}
        for k, v in models.items():
            if isinstance(v, str) and v.strip():
                env[k] = v.strip()
        return env

    if active == "anthropic_direct":
        key = _anthropic_key()
        if not key:
            _missing_anthropic_help()
            sys.exit(1)
        return {
            "ANTHROPIC_BASE_URL": "",
            "ANTHROPIC_AUTH_TOKEN": "",
            "ANTHROPIC_API_KEY": key,
        }

    print(
        f"Unknown active provider {active!r}. Use 'default', 'openrouter', or 'anthropic_direct'.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    if not PROVIDER_FILE.is_file():
        print(f"Missing {PROVIDER_FILE}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(PROVIDER_FILE.read_text(encoding="utf-8"))
    active = str(data.get("active", "default")).strip()

    if not SETTINGS_FILE.is_file():
        print(f"Missing {SETTINGS_FILE}", file=sys.stderr)
        sys.exit(1)

    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))

    if active in ("default", "claude_default", "subscription"):
        settings.pop("env", None)
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {SETTINGS_FILE.relative_to(ROOT)}")
        print(f"  active provider: {active}")
        print("  Removed project env overrides — Claude Code uses normal login / global API key.")
        return

    env = _build_env(active, data)
    settings["env"] = env
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    print(f"Updated {SETTINGS_FILE.relative_to(ROOT)}")
    print(f"  active provider: {active}")
    for k in sorted(env.keys()):
        if "TOKEN" in k or "API_KEY" in k:
            print(f"  {k}: ***")
        else:
            print(f"  {k}: {env[k]}")


if __name__ == "__main__":
    main()
