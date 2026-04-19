# Prompt Registry
> Centralized prompt store for all 24 portfolio projects.
> All prompts are YAML with version frontmatter. Git tracks history.
> Projects import prompts by path — never inline prompts in source code.

## Conventions

### File naming
```
prompts/{project-slug}/v{major}.{minor}/{task-name}.yaml
prompts/shared/v{major}.{minor}/{task-name}.yaml
```

### Versioning rules
- `v1.0` → initial version
- `v1.1` → prompt wording changed, same structure
- `v2.0` → output schema changed (breaking — update all callers)

### How to use in code
```python
from pathlib import Path
import yaml

PROMPTS_ROOT = Path("/Volumes/VeN/Claude-Code-Work/prompts")

def load_prompt(project: str, task: str, version: str = "v1.0") -> dict:
    path = PROMPTS_ROOT / project / version / f"{task}.yaml"
    return yaml.safe_load(path.read_text())

# Usage:
prompt = load_prompt("second-brain-os", "summarize_video")
system = prompt["system"]
user_template = prompt["user"]  # use .format(**vars) to inject content
```

### YAML prompt schema
```yaml
version: "1.0"
project: second-brain-os
task: summarize_video
model_hint: claude-sonnet-4-6    # recommended model, not enforced
max_input_tokens: 7000           # budget for input content
max_output_tokens: 1024
changelog:
  - version: "1.0"
    date: "2026-04-18"
    author: venki
    note: "Initial version"
system: |
  <system prompt here>
user: |
  <user prompt template here — use {variable} for injections>
```

---

## Registry

### second-brain-os
| Task | Current Version | Path |
|------|----------------|------|
| summarize_video | v1.0 | `second-brain-os/v1.0/summarize_video.yaml` |
| summarize_repo | v1.0 | `second-brain-os/v1.0/summarize_repo.yaml` |
| summarize_article | v1.0 | `second-brain-os/v1.0/summarize_article.yaml` |
| daily_note_synthesis | v1.0 | `second-brain-os/v1.0/daily_note_synthesis.yaml` |

### shared
| Task | Current Version | Path |
|------|----------------|------|
| project_mapper | v1.0 | `shared/v1.0/project_mapper.yaml` |

---

*Add new project entries here as each of the 24 projects is built.*
