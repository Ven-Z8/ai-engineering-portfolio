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
    name: str              # bare frontmatter name
    plugin: str | None     # plugin/marketplace slug if recoverable
    source: str            # display string like "superpowers v5.0.7"
    description: str
    path: Path             # path to SKILL.md
    aliases: frozenset[str] = field(default_factory=frozenset)  # how the skill might be referenced in JSONL


def scan_skills(home: Path | None = None) -> list[Skill]:
    """Return all installed skills discovered under `~/.claude/plugins/`."""
    home = home or Path.home()
    plugins_root = home / ".claude" / "plugins"
    if not plugins_root.exists():
        return []

    skills: list[Skill] = []
    for skill_md in plugins_root.rglob("SKILL.md"):
        # Only consider files at the .../skills/<skill>/SKILL.md depth pattern.
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
        key = f"{plugin}:{name}" if plugin else name
        aliases = {name, key}
        if plugin:
            aliases.add(f"{plugin}:{name}")
        skills.append(
            Skill(
                key=key,
                name=name,
                plugin=plugin,
                source=source,
                description=description,
                path=skill_md,
                aliases=frozenset(aliases),
            )
        )

    # De-duplicate: if the same key appears more than once (e.g. cache + marketplace),
    # keep the one with the longest description (proxy for "more complete copy").
    by_key: dict[str, Skill] = {}
    for sk in skills:
        existing = by_key.get(sk.key)
        if existing is None or len(sk.description) > len(existing.description):
            by_key[sk.key] = sk
    return sorted(by_key.values(), key=lambda s: s.key.lower())


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
