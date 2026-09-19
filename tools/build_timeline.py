#!/usr/bin/env python3
"""
Generate the project timeline from git history.

Two views in one HTML file:

  table  One row per game/visual: when it was created, when it last got
         focused attention, how much, and its documented controls checked
         against the inputs its code reads. Sort by any column. This is the
         worklist for the controls parity check.
  chart  Every file as a bubble (sized by lines of code) on a zoomable
         date-vs-size scatter plot.

"Focused" commits touch at most FOCUSED_MAX files — deliberate work on that
item, as opposed to repo-wide sweeps. History follows renames.

Usage:
    python tools/build_timeline.py              # Build & open in browser
    python tools/build_timeline.py --no-open    # Build only
    python tools/build_timeline.py --serve      # Build, open, and serve on :8888
"""

import json, os, subprocess, sys, argparse, webbrowser, http.server
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from controls_vocab import audit, class_source  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "tools" / "timeline.html"

DIRS = {"visuals", "games", "tools", "site"}
FOCUSED_MAX = 5   # a commit touching more files than this is a sweep

# ── data extraction ──────────────────────────────────────────────────

def extract():
    print("Extracting git history …", end=" ", flush=True)

    # Single git log pass, newest first, following renames back in time
    r = subprocess.run(
        ["git", "log", "-M", "--format=COMMIT %aI", "--name-status"],
        capture_output=True, text=True, cwd=ROOT,
    )

    commits = []
    for line in r.stdout.split("\n"):
        if line.startswith("COMMIT "):
            commits.append((line[7:], []))
        elif line.strip() and commits:
            commits[-1][1].append(line.split("\t"))

    # Per-file (by its *current* path): first date, last date, commit counts
    first_date = {}
    last_date  = {}
    last_focused = {}
    commit_count = defaultdict(int)
    focused_count = defaultdict(int)
    alias = {}   # historical path -> current path

    for date, files in commits:
        focused = len(files) <= FOCUSED_MAX
        for parts in files:
            if parts[0].startswith("R") and len(parts) == 3:
                f = alias.get(parts[2], parts[2])
                alias[parts[1]] = f
            else:
                f = alias.get(parts[-1], parts[-1])
            commit_count[f] += 1
            last_date.setdefault(f, date)      # first seen = most recent
            first_date[f] = date               # keeps overwriting = oldest
            if focused:
                focused_count[f] += 1
                last_focused.setdefault(f, date)

    # Build data for tracked files in our directories
    r2 = subprocess.run(
        ["git", "ls-files"] + [f"{d}/" for d in DIRS],
        capture_output=True, text=True, cwd=ROOT,
    )
    tracked = [f for f in r2.stdout.strip().split("\n") if f]

    data = []
    dir_counts = defaultdict(int)
    for f in tracked:
        d = f.split("/")[0]
        if d not in DIRS:
            continue

        created  = first_date.get(f)
        modified = last_date.get(f)
        if not created:
            continue

        # line count
        try:
            lines = sum(1 for _ in open(ROOT / f, errors="ignore"))
        except OSError:
            lines = 0

        basename = os.path.basename(f)
        name = basename
        for ext in (".py", ".json", ".html", ".js", ".css", ".sh",
                    ".service", ".c"):
            name = name.replace(ext, "")

        data.append(dict(
            name=name, file=basename, dir=d,
            created=created, modified=modified or created,
            lines=lines, commits=commit_count.get(f, 0),
            focused=focused_count.get(f, 0),
            last_focused=last_focused.get(f),
            path=f,
        ))
        dir_counts[d] += 1

    parts = [f"{d}/ {dir_counts[d]}" for d in sorted(dir_counts)]
    print(f"{len(data)} files ({', '.join(parts)})")
    return data


def extract_items(files):
    """One row per game/visual in site/guide.json, joined to its file's history
    and audited for controls parity (see tools/controls_vocab.py)."""
    by_path = {d["path"]: d for d in files}
    guide = json.load(open(ROOT / "site" / "guide.json"))
    game_keys = {"arcade", "retro", "modern", "toys", "bar", "2_player",
                 "unique", "game_mix"}
    sharing = defaultdict(int)
    for cat in guide["categories"]:
        for item in cat["items"]:
            sharing[item.get("module")] += 1

    rows = []
    for cat in guide["categories"]:
        for item in cat["items"]:
            hist = by_path.get(item.get("module"))
            if not hist:
                continue
            found = audit(item)
            controls = item.get("controls") or {}
            listed = cat["key"] in ("demos", "titles", "game_mix", "visual_mix")
            flags = []
            if found["unknown_keys"]:
                flags.append("unknown key: " + ", ".join(found["unknown_keys"]))
            if found["documented_not_read"]:
                flags.append("documents unread " + "/".join(found["documented_not_read"]))
            if found["read_not_documented"]:
                flags.append("undocumented " + "/".join(found["read_not_documented"]))
            if found["reads"] and not controls and not listed:
                flags.append("reads input, no controls documented")
            if found["sim_only_keys"]:
                flags.append("sim-only key: " + ", ".join(found["sim_only_keys"]))
            notes = []
            if item.get("stub"):
                notes.append("stub")
            if "custom_exit = True" in class_source(item["cls"], item["module"]):
                notes.append("own exit")
            if sharing[item["module"]] > 1:
                notes.append(f"file shared by {sharing[item['module']]}")
            rows.append(dict(
                name=item["name"], cls=item["cls"], module=item["module"],
                cat=cat["key"], kind="game" if cat["key"] in game_keys else "visual",
                created=hist["created"], last_focused=hist["last_focused"],
                modified=hist["modified"], focused=hist["focused"],
                commits=hist["commits"], lines=hist["lines"],
                controls=controls, reads=found["reads"],
                flags=flags, notes=notes,
            ))
    flagged = sum(1 for r in rows if r["flags"])
    print(f"{len(rows)} catalog items, {flagged} with controls flags")
    return rows

# ── table view (plain strings: no f-string brace doubling) ──────────

TABLE_CSS = """
  #table-wrap {
    position: absolute; top: 48px; left: 0; right: 0; bottom: 0;
    overflow: auto; display: none;
  }
  body.view-table #table-wrap { display: block; }
  body.view-table #canvas-wrap, body.view-table #help,
  body.view-table .chart-only { display: none; }
  body.view-chart .table-only { display: none; }

  #t-bar {
    position: sticky; top: 0; z-index: 20;
    display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
    padding: 10px 16px; background: #0a0a0f; border-bottom: 1px solid #222;
  }
  #t-search {
    background: #111118; border: 1px solid #333; border-radius: 12px;
    color: #ddd; font-family: inherit; font-size: 12px;
    padding: 5px 12px; width: 220px;
  }
  #t-search:focus { outline: none; border-color: #4caf50; }
  #t-count { font-size: 11px; color: #777; margin-left: auto; }
  .chip.active { color: #fff; border-color: #4caf50; background: #4caf5018; }

  table { border-collapse: collapse; width: 100%; font-size: 12px; }
  thead th {
    position: sticky; top: 47px; z-index: 10;
    background: #111118; color: #999; font-weight: normal; text-align: left;
    padding: 8px 10px; border-bottom: 1px solid #333;
    cursor: pointer; white-space: nowrap; user-select: none;
  }
  thead th:hover { color: #fff; }
  thead th.sorted { color: #6fcf73; }
  thead th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
  tbody td { padding: 7px 10px; border-bottom: 1px solid #1a1a22; vertical-align: top; }
  tbody tr:hover td { background: #12121a; }
  td.name { color: #fff; white-space: nowrap; }
  td.name small { display: block; color: #666; font-size: 10px; margin-top: 2px; }
  td.date { white-space: nowrap; color: #aaa; }
  td.never { color: #e57373; }
  .kind-game { color: #64b5f6; } .kind-visual { color: #6fcf73; }
  .ctl { display: grid; grid-template-columns: max-content 1fr; gap: 2px 8px; max-width: 460px; }
  .ctl b { color: #ffb74d; font-weight: normal; white-space: nowrap; }
  .ctl span { color: #aaa; }
  .none { color: #555; }
  .reads { color: #888; white-space: nowrap; }
  .flag { display: block; color: #e57373; margin-bottom: 2px; }
  .note { display: inline-block; color: #777; border: 1px solid #2a2a33;
          border-radius: 8px; padding: 0 6px; margin: 0 4px 2px 0; font-size: 10px; }
  .bar { display: inline-block; height: 6px; background: #4caf50; border-radius: 3px;
         margin-right: 6px; vertical-align: middle; opacity: 0.7; }
"""

TABLE_HTML = """
<div id="table-wrap">
  <div id="t-bar">
    <input id="t-search" type="search" placeholder="filter name, file, control…">
    <button class="filter-btn chip active" data-kind="visual">visuals</button>
    <button class="filter-btn chip active" data-kind="game">games</button>
    <button class="filter-btn chip" id="t-flagged">flagged only</button>
    <button class="filter-btn chip" id="t-untouched">never refined</button>
    <span id="t-count"></span>
  </div>
  <table>
    <thead><tr>
      <th data-key="name">name</th>
      <th data-key="cat">category</th>
      <th data-key="created">created</th>
      <th data-key="last_focused">last focused work</th>
      <th data-key="focused" class="num" title="commits touching 5 files or fewer">focused</th>
      <th data-key="commits" class="num" title="all commits, sweeps included">all</th>
      <th data-key="lines" class="num">lines</th>
      <th data-key="ncontrols">documented controls</th>
      <th data-key="nreads">code reads</th>
      <th data-key="nflags">parity flags</th>
    </tr></thead>
    <tbody id="t-body"></tbody>
  </table>
</div>
"""

TABLE_JS = """
// ── table view ──
let tSort = { key: 'created', dir: 1 };
let tKinds = { visual: true, game: true };
let tFlagged = false, tUntouched = false, tQuery = '';

function esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function day(iso) { return iso ? iso.slice(0, 10) : null; }

ITEMS.forEach(r => {
  r.ncontrols = Object.keys(r.controls).length;
  r.nreads = r.reads.length;
  r.nflags = r.flags.length;
  r.hay = [r.name, r.cls, r.module, r.cat, Object.keys(r.controls).join(' '),
           Object.values(r.controls).join(' '), r.flags.join(' '), r.notes.join(' ')]
          .join(' ').toLowerCase();
});
const maxFocused = Math.max(1, ...ITEMS.map(r => r.focused));

function tRows() {
  const rows = ITEMS.filter(r =>
    tKinds[r.kind] && (!tFlagged || r.nflags) && (!tUntouched || !r.focused) &&
    (!tQuery || r.hay.includes(tQuery)));
  const k = tSort.key;
  rows.sort((a, b) => {
    let x = a[k], y = b[k];
    if (x == null) x = ''; if (y == null) y = '';
    const c = (typeof x === 'number') ? x - y : String(x).localeCompare(String(y));
    // ties: oldest and least-touched first — the parity worklist order
    return (c * tSort.dir) || a.created.localeCompare(b.created) || (a.focused - b.focused);
  });
  return rows;
}

function drawTable() {
  const rows = tRows();
  document.getElementById('t-count').textContent =
    rows.length + ' of ' + ITEMS.length + ' items · ' +
    rows.filter(r => r.nflags).length + ' flagged · ' +
    rows.filter(r => !r.focused).length + ' never refined';
  document.querySelectorAll('thead th').forEach(th => {
    const on = th.dataset.key === tSort.key;
    th.classList.toggle('sorted', on);
    th.textContent = th.textContent.replace(/ [▲▼]$/, '') + (on ? (tSort.dir > 0 ? ' ▲' : ' ▼') : '');
  });
  document.getElementById('t-body').innerHTML = rows.map(r => {
    const ctl = r.ncontrols
      ? '<div class="ctl">' + Object.entries(r.controls).map(([k, v]) =>
          '<b>' + esc(k) + '</b><span>' + esc(v) + '</span>').join('') + '</div>'
      : '<span class="none">—</span>';
    return '<tr>' +
      '<td class="name"><span class="kind-' + r.kind + '">' + esc(r.name) + '</span>' +
        '<small>' + esc(r.module) + ' · ' + esc(r.cls) + '</small></td>' +
      '<td>' + esc(r.cat) + '</td>' +
      '<td class="date">' + day(r.created) + '</td>' +
      (r.last_focused ? '<td class="date">' + day(r.last_focused) + '</td>'
                      : '<td class="date never">never</td>') +
      '<td class="num"><span class="bar" style="width:' + Math.round(40 * r.focused / maxFocused) +
        'px"></span>' + r.focused + '</td>' +
      '<td class="num">' + r.commits + '</td>' +
      '<td class="num">' + r.lines.toLocaleString() + '</td>' +
      '<td>' + ctl + '</td>' +
      '<td class="reads">' + (r.nreads ? esc(r.reads.join(' ')) : '<span class="none">nothing</span>') + '</td>' +
      '<td>' + r.flags.map(f => '<span class="flag">' + esc(f) + '</span>').join('') +
        r.notes.map(n => '<span class="note">' + esc(n) + '</span>').join('') + '</td>' +
      '</tr>';
  }).join('');
}

function initTable() {
  document.querySelectorAll('thead th').forEach(th => th.addEventListener('click', () => {
    const k = th.dataset.key;
    if (tSort.key === k) tSort.dir = -tSort.dir;
    else tSort = { key: k, dir: (k === 'name' || k === 'cat' || k === 'created' || k === 'last_focused') ? 1 : -1 };
    drawTable();
  }));
  document.querySelectorAll('.chip[data-kind]').forEach(b => b.addEventListener('click', () => {
    tKinds[b.dataset.kind] = !tKinds[b.dataset.kind];
    b.classList.toggle('active', tKinds[b.dataset.kind]);
    drawTable();
  }));
  document.getElementById('t-flagged').addEventListener('click', e => {
    tFlagged = !tFlagged; e.target.classList.toggle('active', tFlagged); drawTable();
  });
  document.getElementById('t-untouched').addEventListener('click', e => {
    tUntouched = !tUntouched; e.target.classList.toggle('active', tUntouched); drawTable();
  });
  document.getElementById('t-search').addEventListener('input', e => {
    tQuery = e.target.value.trim().toLowerCase(); drawTable();
  });
  document.getElementById('view-toggle').addEventListener('click', () => {
    const toChart = document.body.classList.contains('view-table');
    document.body.className = toChart ? 'view-chart' : 'view-table';
    document.getElementById('view-toggle').textContent = toChart ? 'view: chart' : 'view: table';
    if (toChart) resize();
  });
  drawTable();
}
"""

# ── HTML template ────────────────────────────────────────────────────

def build_html(data, items):
    data_json = json.dumps(data)
    items_json = json.dumps(items)
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LED Arcade — Creation Timeline</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0f;
    color: #ccc;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    overflow: hidden;
    height: 100vh;
  }}

  #toolbar {{
    position: fixed; top: 0; left: 0; right: 0;
    height: 48px;
    background: #111118;
    border-bottom: 1px solid #222;
    display: flex; align-items: center;
    padding: 0 16px;
    z-index: 100;
    gap: 12px;
  }}
  #toolbar h1 {{
    font-size: 14px; color: #fff; margin-right: 24px; white-space: nowrap;
  }}
  .filter-btn {{
    padding: 4px 12px;
    border-radius: 12px;
    border: 1px solid #333;
    background: transparent;
    color: #888;
    font-family: inherit;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .filter-btn.active {{ border-color: currentColor; color: #fff; }}
  .filter-btn[data-dir="visuals"].active {{ color: #4caf50; border-color: #4caf50; background: #4caf5018; }}
  .filter-btn[data-dir="games"].active   {{ color: #2196f3; border-color: #2196f3; background: #2196f318; }}
  .filter-btn[data-dir="tools"].active   {{ color: #ab47bc; border-color: #ab47bc; background: #ab47bc18; }}
  .filter-btn[data-dir="site"].active    {{ color: #ff9800; border-color: #ff9800; background: #ff980018; }}

  .tb-spacer {{ flex: 1; }}

  .tb-btn {{
    padding: 4px 12px;
    border-radius: 12px;
    border: 1px solid #444;
    background: transparent;
    color: #aaa;
    font-family: inherit;
    font-size: 11px;
    cursor: pointer;
  }}
  .tb-btn:hover {{ color: #fff; border-color: #666; }}

  #canvas-wrap {{
    position: absolute;
    top: 48px; left: 0; right: 0; bottom: 0;
  }}

  canvas {{ display: block; cursor: grab; }}

  #tooltip {{
    position: fixed;
    pointer-events: none;
    background: #1a1a24;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.6;
    display: none;
    z-index: 200;
    max-width: 280px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  #tooltip .tt-name {{ font-size: 14px; font-weight: bold; color: #fff; }}
  #tooltip .tt-dir  {{ font-size: 11px; opacity: 0.5; }}
  #tooltip .tt-stat {{ color: #aaa; }}
  #tooltip .tt-stat span {{ color: #fff; }}

  #help {{
    position: fixed;
    bottom: 12px; right: 16px;
    font-size: 10px;
    color: #444;
    z-index: 100;
  }}
{TABLE_CSS}</style>
</head>
<body class="view-table">

<div id="toolbar">
  <h1>LED Arcade Timeline</h1>
  <button class="filter-btn active chart-only" data-dir="visuals">visuals</button>
  <button class="filter-btn active chart-only" data-dir="games">games</button>
  <button class="filter-btn active chart-only" data-dir="tools">tools</button>
  <button class="filter-btn active chart-only" data-dir="site">site</button>
  <div class="tb-spacer"></div>
  <button class="tb-btn chart-only" id="y-axis-toggle">Y: lines</button>
  <button class="tb-btn chart-only" id="reset-btn">reset zoom</button>
  <button class="tb-btn" id="view-toggle">view: table</button>
</div>

<div id="canvas-wrap"><canvas id="c"></canvas></div>
{TABLE_HTML}<div id="tooltip"></div>
<div id="help">scroll to zoom &middot; drag to pan &middot; click buttons to filter</div>

<script>
const DATA = {data_json};
const ITEMS = {items_json};

const DIR_COLORS = {{
  visuals: {{ dot: '#4caf50', glow: '#4caf5044', label: '#6fcf73' }},
  games:   {{ dot: '#2196f3', glow: '#2196f344', label: '#64b5f6' }},
  tools:   {{ dot: '#ab47bc', glow: '#ab47bc44', label: '#ce93d8' }},
  site:    {{ dot: '#ff9800', glow: '#ff980044', label: '#ffb74d' }},
}};

let yMode = 'lines';
let filters = {{ visuals: true, games: true, tools: true, site: true }};
let transform = {{ x: 0, y: 0, k: 1 }};
let canvas, ctx, W, H;
let hoveredItem = null;
let dragging = false, dragStart, dragTransformStart;

let minDate, maxDate, maxLines, maxCommits;

// ── init ──

function init() {{
  canvas = document.getElementById('c');
  ctx = canvas.getContext('2d');

  DATA.forEach(d => {{
    d.createdMs  = new Date(d.created).getTime();
    d.modifiedMs = new Date(d.modified).getTime();
  }});

  computeBounds();
  updateCounts();
  resize();
  window.addEventListener('resize', resize);

  canvas.addEventListener('wheel', onWheel, {{ passive: false }});
  canvas.addEventListener('mousedown', onMouseDown);
  canvas.addEventListener('mousemove', onMouseMove);
  canvas.addEventListener('mouseup',   onMouseUp);
  canvas.addEventListener('mouseleave', () => {{
    dragging = false; hoveredItem = null; hideTooltip(); draw();
  }});

  document.querySelectorAll('.filter-btn[data-dir]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      filters[btn.dataset.dir] = !filters[btn.dataset.dir];
      btn.classList.toggle('active', filters[btn.dataset.dir]);
      updateCounts();
      draw();
    }});
  }});

  document.getElementById('y-axis-toggle').addEventListener('click', () => {{
    yMode = yMode === 'lines' ? 'commits' : 'lines';
    document.getElementById('y-axis-toggle').textContent = 'Y: ' + yMode;
    transform = {{ x: 0, y: 0, k: 1 }};
    draw();
  }});

  document.getElementById('reset-btn').addEventListener('click', () => {{
    transform = {{ x: 0, y: 0, k: 1 }};
    draw();
  }});
}}

function resize() {{
  const wrap = document.getElementById('canvas-wrap');
  W = wrap.clientWidth;
  H = wrap.clientHeight;
  canvas.width  = W * devicePixelRatio;
  canvas.height = H * devicePixelRatio;
  canvas.style.width  = W + 'px';
  canvas.style.height = H + 'px';
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  draw();
}}

function computeBounds() {{
  minDate = Infinity; maxDate = -Infinity;
  maxLines = 0; maxCommits = 0;
  for (const d of DATA) {{
    if (d.createdMs < minDate) minDate = d.createdMs;
    if (d.createdMs > maxDate) maxDate = d.createdMs;
    if (d.lines    > maxLines)   maxLines   = d.lines;
    if (d.commits  > maxCommits) maxCommits = d.commits;
  }}
}}

function updateCounts() {{
  document.querySelectorAll('.filter-btn[data-dir]').forEach(btn => {{
    const dir = btn.dataset.dir;
    const n = DATA.filter(d => d.dir === dir).length;
    btn.textContent = dir + ' (' + n + ')';
  }});
}}

// ── coordinate mapping ──

const M = {{ left: 60, right: 40, top: 30, bottom: 50 }};

function getYVal(d) {{ return yMode === 'lines' ? d.lines : d.commits; }}
function getMaxY()  {{ return yMode === 'lines' ? maxLines : maxCommits; }}

function dataToScreen(dateMs, yVal) {{
  const maxY = getMaxY();
  const pw = W - M.left - M.right;
  const ph = H - M.top  - M.bottom;
  const dr = maxDate - minDate || 1;
  let sx = M.left + ((dateMs - minDate) / dr) * pw;
  let sy = M.top  + ph - (yVal / (maxY * 1.1)) * ph;
  return {{ x: sx * transform.k + transform.x,
           y: sy * transform.k + transform.y }};
}}

function bubbleR(item) {{
  const r = Math.sqrt(item.lines) * 0.4;
  return Math.max(3, Math.min(r, 40)) * Math.min(transform.k, 3);
}}

// ── drawing ──

function draw() {{
  if (!ctx) return;
  ctx.clearRect(0, 0, W, H);
  const maxY = getMaxY();
  if (maxY === 0) return;
  drawGrid();

  const visible = DATA.filter(d => filters[d.dir]);
  for (const item of visible) {{
    const {{ x, y }} = dataToScreen(item.createdMs, getYVal(item));
    if (x < -100 || x > W+100 || y < -100 || y > H+100) continue;

    const r = bubbleR(item);
    const c = DIR_COLORS[item.dir];
    const hov = hoveredItem === item;

    // glow
    if (r > 5 || hov) {{
      ctx.beginPath();
      ctx.arc(x, y, r + (hov ? 8 : 4), 0, Math.PI*2);
      ctx.fillStyle = hov ? c.dot + '55' : c.glow;
      ctx.fill();
    }}
    // dot
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fillStyle = hov ? '#fff' : c.dot;
    ctx.globalAlpha = hov ? 1 : 0.8;
    ctx.fill();
    ctx.globalAlpha = 1;

    // label
    if (hov || r * transform.k > 6 || transform.k > 1.5) {{
      const fs = Math.max(8, Math.min(11, 9 * transform.k));
      ctx.font = fs + 'px Menlo,Monaco,monospace';
      ctx.fillStyle = hov ? '#fff' : c.label;
      ctx.globalAlpha = hov ? 1 : Math.min(1, 0.3 + transform.k*0.3);
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(item.name, x + r + 4, y);
      ctx.globalAlpha = 1;
    }}
  }}
}}

function drawGrid() {{
  const maxY = getMaxY();
  const pw = W - M.left - M.right;
  const ph = H - M.top  - M.bottom;
  ctx.strokeStyle = '#ffffff08';
  ctx.lineWidth = 1;
  ctx.font = '10px Menlo,Monaco,monospace';
  ctx.fillStyle = '#555';

  // Y
  for (const v of niceSteps(0, maxY*1.1, 8)) {{
    const {{ y }} = dataToScreen(minDate, v);
    if (y < M.top-20 || y > H-M.bottom+20) continue;
    ctx.beginPath();
    ctx.moveTo(M.left * transform.k + transform.x, y);
    ctx.lineTo(W, y);
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(fmtNum(v),
      Math.max(8, M.left * transform.k + transform.x - 8), y);
  }}

  // X
  const vdr = (maxDate - minDate) / transform.k;
  let iv;
  if      (vdr < 3*864e5)  iv = 6*36e5;
  else if (vdr < 14*864e5) iv = 864e5;
  else if (vdr < 45*864e5) iv = 3*864e5;
  else                     iv = 7*864e5;
  let t = Math.ceil(minDate / iv) * iv;
  while (t <= maxDate + iv) {{
    const {{ x }} = dataToScreen(t, 0);
    if (x >= M.left-20 && x <= W+20) {{
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      const label = new Date(t).toLocaleDateString('en-US', {{
        month: 'short', day: 'numeric',
        ...(iv < 864e5 ? {{ hour: 'numeric' }} : {{}})
      }});
      ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      ctx.fillText(label, x, Math.min(H - M.bottom + 10, H - 14));
    }}
    t += iv;
  }}

  // axis label
  ctx.fillStyle = '#666'; ctx.font = '11px Menlo,Monaco,monospace';
  ctx.save(); ctx.translate(14, H/2); ctx.rotate(-Math.PI/2);
  ctx.textAlign = 'center';
  ctx.fillText(yMode === 'lines' ? 'lines of code' : 'commits', 0, 0);
  ctx.restore();
}}

function niceSteps(lo, hi, n) {{
  const rough = (hi-lo)/n;
  const mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const f = rough/mag;
  const step = (f<=1.5?1:f<=3.5?2:f<=7.5?5:10)*mag;
  const out = [];
  let v = Math.ceil(lo/step)*step;
  while (v <= hi) {{ out.push(v); v += step; }}
  return out;
}}

function fmtNum(n) {{
  return n >= 1000 ? (n/1000).toFixed(n>=10000?0:1)+'k' : String(Math.round(n));
}}

// ── interaction ──

function onWheel(e) {{
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const f = e.deltaY > 0 ? 0.9 : 1.1;
  const nk = Math.max(0.5, Math.min(transform.k * f, 50));
  transform.x = mx - (mx - transform.x) * (nk / transform.k);
  transform.y = my - (my - transform.y) * (nk / transform.k);
  transform.k = nk;
  draw();
}}

function onMouseDown(e) {{
  dragging = true;
  dragStart = {{ x: e.clientX, y: e.clientY }};
  dragTransformStart = {{ x: transform.x, y: transform.y }};
  canvas.style.cursor = 'grabbing';
}}

function onMouseMove(e) {{
  if (dragging) {{
    transform.x = dragTransformStart.x + (e.clientX - dragStart.x);
    transform.y = dragTransformStart.y + (e.clientY - dragStart.y);
    draw();
    return;
  }}
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  let closest = null, best = Infinity;
  for (const item of DATA.filter(d => filters[d.dir])) {{
    const {{ x, y }} = dataToScreen(item.createdMs, getYVal(item));
    const dist = Math.hypot(mx-x, my-y);
    if (dist < bubbleR(item)+6 && dist < best) {{ closest = item; best = dist; }}
  }}
  if (closest !== hoveredItem) {{
    hoveredItem = closest;
    canvas.style.cursor = closest ? 'pointer' : 'grab';
    if (closest) showTooltip(closest, e.clientX, e.clientY);
    else hideTooltip();
    draw();
  }} else if (closest) posTooltip(e.clientX, e.clientY);
}}

function onMouseUp() {{
  dragging = false;
  canvas.style.cursor = hoveredItem ? 'pointer' : 'grab';
}}

function showTooltip(item, mx, my) {{
  const tip = document.getElementById('tooltip');
  const fmt = d => new Date(d).toLocaleDateString('en-US', {{
    weekday:'short', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'
  }});
  const age = Math.round((new Date(item.modified) - new Date(item.created)) / 864e5);
  tip.innerHTML =
    '<div class="tt-name">' + item.name + '</div>' +
    '<div class="tt-dir">'  + item.dir + '/' + item.file + '</div>' +
    '<div class="tt-stat"><span>' + item.lines.toLocaleString() + '</span> lines · ' +
        '<span>' + item.commits + '</span> commits</div>' +
    '<div class="tt-stat">created <span>' + fmt(item.created)  + '</span></div>' +
    '<div class="tt-stat">last touched <span>' + fmt(item.modified) + '</span></div>' +
    (age > 0 ? '<div class="tt-stat">active span: <span>' + age + 'd</span></div>' : '');
  tip.style.display = 'block';
  posTooltip(mx, my);
}}

function posTooltip(mx, my) {{
  const tip = document.getElementById('tooltip');
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  let x = mx + 16, y = my - 10;
  if (x + tw > innerWidth - 8) x = mx - tw - 16;
  if (y + th > innerHeight - 8) y = innerHeight - th - 8;
  if (y < 56) y = 56;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}}

function hideTooltip() {{
  document.getElementById('tooltip').style.display = 'none';
}}

{TABLE_JS}
init();
initTable();
</script>
</body>
</html>"""

# ── main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build interactive git timeline")
    parser.add_argument("--no-open", action="store_true",
                        help="Don't open browser automatically")
    parser.add_argument("--serve", action="store_true",
                        help="Start a local server on :8888 after building")
    parser.add_argument("-o", "--output", type=str, default=str(OUT),
                        help=f"Output path (default: {OUT})")
    args = parser.parse_args()

    data = extract()
    html = build_html(data, extract_items(data))

    out_path = Path(args.output)
    out_path.write_text(html)
    print(f"\nWritten to {out_path}")

    if args.serve:
        os.chdir(out_path.parent)
        port = 8888
        handler = http.server.SimpleHTTPRequestHandler
        server = http.server.HTTPServer(("", port), handler)
        print(f"Serving on http://localhost:{port}/{out_path.name}")
        if not args.no_open:
            webbrowser.open(f"http://localhost:{port}/{out_path.name}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    elif not args.no_open:
        webbrowser.open(f"file://{out_path.resolve()}")

if __name__ == "__main__":
    main()
