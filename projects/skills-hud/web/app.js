"use strict";

const state = {
  rows: [],
  unmatchedCount: 0,
  sort: { key: "recent", dir: "desc" },
  filter: "",
  unused: false,
  recent: false,
};

const COLUMNS = [
  { key: "key",         label: "Skill",        cmp: (a, b) => a.key.localeCompare(b.key) },
  { key: "source",      label: "Source",       cmp: (a, b) => (a.source || "").localeCompare(b.source || "") },
  { key: "recent",      label: "30d",          num: true, cmp: (a, b) => a.recent - b.recent },
  { key: "total",       label: "All-time",     num: true, cmp: (a, b) => a.total - b.total },
  { key: "last_used",   label: "Last used",    cmp: (a, b) =>
      (new Date(a.last_used || 0).getTime()) - (new Date(b.last_used || 0).getTime()) },
  { key: "description", label: "What it does" },
];

const SOURCE_LABEL = {
  tool: "explicit Skill tool call from the assistant",
  cmd:  "slash-command you typed",
  auto: "auto-loaded by SessionStart hooks (you didn't choose it)",
};

function escape(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]
  ));
}

function fmtRel(iso) {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "—";
  const days = (Date.now() - t) / 86400000;
  if (days < 1) return "today";
  if (days < 2) return "yesterday";
  if (days < 30) return `${Math.floor(days)}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

function breakdownChips(bd) {
  if (!bd) return "";
  const parts = [];
  for (const src of ["tool", "cmd", "auto"]) {
    const n = bd[src] || 0;
    if (n > 0) {
      parts.push(
        `<span class="src-chip src-${src}" title="${escape(SOURCE_LABEL[src])}">${src} ${n}</span>`
      );
    }
  }
  return parts.length ? `<div class="chips">${parts.join("")}</div>` : "";
}

function applyFilters() {
  const q = state.filter.trim().toLowerCase();
  let rows = state.rows.slice();
  if (q) {
    rows = rows.filter(r =>
      r.key.toLowerCase().includes(q) ||
      (r.source || "").toLowerCase().includes(q) ||
      (r.description || "").toLowerCase().includes(q)
    );
  }
  if (state.unused) rows = rows.filter(r => r.total === 0);
  if (state.recent) rows = rows.filter(r => r.recent > 0);

  const col = COLUMNS.find(c => c.key === state.sort.key);
  if (col && col.cmp) {
    rows.sort(col.cmp);
    if (state.sort.dir === "desc") rows.reverse();
  }
  return rows;
}

function render() {
  const rows = applyFilters();
  const head = "<tr>" + COLUMNS.map(c => {
    let cls = c.num ? "num " : "";
    if (c.key === state.sort.key) cls += "sorted " + (state.sort.dir === "asc" ? "asc" : "");
    return `<th data-key="${c.key}" class="${cls.trim()}">${escape(c.label)}</th>`;
  }).join("") + "</tr>";

  const body = rows.map(r => `
    <tr class="${r.total === 0 ? "unused" : ""}">
      <td>
        <div class="key">
          ${escape(r.key)}
          <span class="kind kind-${r.kind || "skill"}">${escape(r.kind || "skill")}</span>
        </div>
        ${breakdownChips(r.breakdown)}
      </td>
      <td><span class="src">${escape(r.source || "")}</span></td>
      <td class="num">${r.recent}</td>
      <td class="num">${r.total}</td>
      <td>${escape(fmtRel(r.last_used))}</td>
      <td class="desc">${escape(r.description || "")}</td>
    </tr>
  `).join("");

  document.getElementById("grid").innerHTML =
    `<table><thead>${head}</thead><tbody>${body || `<tr><td colspan="6" class="pad">No skills match.</td></tr>`}</tbody></table>`;

  document.querySelectorAll("th[data-key]").forEach(th => {
    th.addEventListener("click", () => {
      const k = th.dataset.key;
      if (state.sort.key === k) {
        state.sort.dir = state.sort.dir === "asc" ? "desc" : "asc";
      } else {
        state.sort.key = k;
        state.sort.dir = (k === "key" || k === "source" || k === "description") ? "asc" : "desc";
      }
      render();
    });
  });
}

async function load() {
  try {
    const r = await fetch("/api/skills");
    const data = await r.json();
    state.rows = data.skills || [];
    state.unmatchedCount = data.unmatched_count || 0;
    const used = state.rows.filter(s => s.total > 0).length;
    const unused = state.rows.length - used;
    const earned = state.rows.filter(s => (s.breakdown?.tool || 0) + (s.breakdown?.cmd || 0) > 0).length;
    const parts = [
      `${data.total_skills} skills`,
      `<span class="badge tone-blue">${earned} earned</span>`,
      `<span class="badge tone-grey">${used - earned} auto-only</span>`,
      `<span class="badge tone-zero">${unused} unused</span>`,
      `<span class="badge">${data.sessions_scanned} sessions</span>`,
    ];
    if (state.unmatchedCount > 0) {
      parts.push(`<span class="badge tone-warn" title="Slash commands or skill names found in logs but not matching any installed skill (e.g. built-in CLI commands like /plugin, /login)">${state.unmatchedCount} unmatched</span>`);
    }
    document.getElementById("meta").innerHTML = parts.join(" ");
    render();
  } catch (err) {
    document.getElementById("grid").innerHTML =
      `<div class="pad">Failed to load: ${escape(err.message || err)}</div>`;
  }
}

document.getElementById("filter").addEventListener("input", e => {
  state.filter = e.target.value;
  render();
});
document.getElementById("onlyUnused").addEventListener("change", e => {
  state.unused = e.target.checked;
  render();
});
document.getElementById("recentOnly").addEventListener("change", e => {
  state.recent = e.target.checked;
  render();
});

load();
