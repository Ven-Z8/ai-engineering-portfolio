"""Find installed Claude Code skills and parse their frontmatter.

A skill is a directory under `~/.claude/plugins/` containing a `SKILL.md` file
whose YAML frontmatter has a `name` field. We collect each skill's canonical
key (the form most likely to appear in session logs), a human-readable source
label (plugin + version when recoverable), and the description.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Skill:
    key: str               # canonical form: "plugin:name" if plugin else "name"
    name: str              # bare frontmatter name (or filename stem for commands)
    plugin: str | None     # plugin/marketplace slug if recoverable
    source: str            # display string like "superpowers v5.0.7"
    description: str
    path: Path             # path to the source markdown file
    kind: str = "skill"    # "skill" (SKILL.md) or "command" (commands/*.md)
    aliases: frozenset[str] = field(default_factory=frozenset)  # how it might be referenced in JSONL


def scan_skills(home: Path | None = None) -> list[Skill]:
    """Return all installed skills and commands discovered under `~/.claude/plugins/`.

    Both SKILL.md files and commands/*.md files are surfaced because Claude Code's
    user-facing slash-command list flattens them together. From the HUD's point of
    view they are both "things you can invoke," and the `kind` field distinguishes them.
    """
    home = home or Path.home()
    plugins_root = home / ".claude" / "plugins"
    if not plugins_root.exists():
        return []

    entries: list[Skill] = []

    # 1. SKILL.md files (proper skills)
    for skill_md in plugins_root.rglob("SKILL.md"):
        if skill_md.parent.parent.name != "skills":
            continue
        parsed = _parse_frontmatter(skill_md)
        if not parsed or "name" not in parsed:
            continue
        name = str(parsed["name"]).strip()
        if not name:
            continue
        plugin, source = _derive_source(skill_md, plugins_root)
        description = str(parsed.get("description", "")).strip()
        entries.append(_make_entry(name, plugin, source, description, skill_md, kind="skill"))

    # 2. commands/*.md files (slash commands listed alongside skills)
    for cmd_md in plugins_root.rglob("*.md"):
        if cmd_md.name == "SKILL.md":
            continue
        if cmd_md.parent.name != "commands":
            continue
        name = cmd_md.stem
        if not name or name.startswith("_"):
            continue
        parsed = _parse_frontmatter(cmd_md) or {}
        description = str(parsed.get("description", "")).strip()
        plugin, source = _derive_source(cmd_md, plugins_root)
        entries.append(_make_entry(name, plugin, source, description, cmd_md, kind="command"))

    # De-duplicate: if the same key appears more than once (e.g. cache + marketplace),
    # keep the one with the longest description (proxy for "more complete copy").
    by_key: dict[str, Skill] = {}
    for sk in entries:
        existing = by_key.get(sk.key)
        if existing is None or len(sk.description) > len(existing.description):
            by_key[sk.key] = sk
    return sorted(by_key.values(), key=lambda s: s.key.lower())


def _make_entry(
    name: str,
    plugin: str | None,
    source: str,
    description: str,
    path: Path,
    kind: str,
) -> Skill:
    key = f"{plugin}:{name}" if plugin else name
    aliases = {name, key}
    if plugin:
        aliases.add(f"{plugin}:{name}")
    return Skill(
        key=key,
        name=name,
        plugin=plugin,
        source=source,
        description=description,
        path=path,
        kind=kind,
        aliases=frozenset(aliases),
    )


def _parse_frontmatter(skill_md: Path) -> dict | None:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    raw = text[3:end].strip()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _derive_source(skill_md: Path, plugins_root: Path) -> tuple[str | None, str]:
    """Return (plugin_slug, display_source).

    Path shapes we handle:
      cache/<marketplace>/<plugin>/<version>/skills/<skill>/SKILL.md
      marketplaces/<marketplace>/plugins/<plugin>/skills/<skill>/SKILL.md
      marketplaces/<marketplace>/external_plugins/<plugin>/skills/<skill>/SKILL.md
      marketplaces/<marketplace>/skills/<skill>/SKILL.md
    """
    try:
        rel = skill_md.relative_to(plugins_root)
    except ValueError:
        return None, skill_md.parent.parent.name
    parts = rel.parts

    if parts and parts[0] == "cache":
        # cache/<marketplace>/<plugin>/<version>/skills/<skill>/SKILL.md
        plugin = parts[2] if len(parts) > 2 else None
        version = parts[3] if len(parts) > 3 else None
        if plugin and version:
            return plugin, f"{plugin} v{version}"
        return plugin, plugin or ""

    if parts and parts[0] == "marketplaces":
        marketplace = parts[1] if len(parts) > 1 else None
        if len(parts) > 3 and parts[2] in ("plugins", "external_plugins"):
            plugin = parts[3]
            return plugin, f"{plugin} ({marketplace})" if marketplace else plugin
        # marketplaces/<marketplace>/skills/<skill>/SKILL.md
        return marketplace, marketplace or ""

    return None, skill_md.parent.parent.name
