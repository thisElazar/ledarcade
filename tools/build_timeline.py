#!/usr/bin/env python3
"""
Generate an interactive timeline visualization of the project's git history.

Shows every file as a bubble (sized by lines of code) on a zoomable
date-vs-size scatter plot.  Hover for details, filter by directory,
toggle Y axis between lines and commits.

Usage:
    python tools/build_timeline.py              # Build & open in browser
    python tools/build_timeline.py --no-open    # Build only
    python tools/build_timeline.py --serve      # Build, open, and serve on :8888
"""

import json, os, subprocess, sys, argparse, webbrowser, http.server
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "tools" / "timeline.html"

DIRS = {"visuals", "games", "tools", "site"}

# ── data extraction ──────────────────────────────────────────────────

def extract():
    print("Extracting git history …", end=" ", flush=True)

    # Single git log pass: get every commit's date and its files
    r = subprocess.run(
        ["git", "log", "--format=COMMIT %aI", "--name-only"],
        capture_output=True, text=True, cwd=ROOT,
    )

    # Per-file: track first date, last date, commit count
    first_date = {}   # file -> earliest ISO date
    last_date  = {}   # file -> latest ISO date
    commit_count = defaultdict(int)

    current_date = None
    for line in r.stdout.split("\n"):
        if line.startswith("COMMIT "):
            current_date = line[7:]
        elif line and current_date:
            f = line
            commit_count[f] += 1
            if f not in last_date:
                last_date[f] = current_date   # first seen = most recent
            first_date[f] = current_date       # keeps overwriting = oldest

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
        ))
        dir_counts[d] += 1

    parts = [f"{d}/ {dir_counts[d]}" for d in sorted(dir_counts)]
    print(f"{len(data)} files ({', '.join(parts)})")
    return data

# ── HTML template ────────────────────────────────────────────────────

def build_html(data):
    data_json = json.dumps(data)
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
</style>
</head>
<body>

<div id="toolbar">
  <h1>LED Arcade Timeline</h1>
  <button class="filter-btn active" data-dir="visuals">visuals</button>
  <button class="filter-btn active" data-dir="games">games</button>
  <button class="filter-btn active" data-dir="tools">tools</button>
  <button class="filter-btn active" data-dir="site">site</button>
  <div class="tb-spacer"></div>
  <button class="tb-btn" id="y-axis-toggle">Y: lines</button>
  <button class="tb-btn" id="reset-btn">reset zoom</button>
</div>

<div id="canvas-wrap"><canvas id="c"></canvas></div>
<div id="tooltip"></div>
<div id="help">scroll to zoom &middot; drag to pan &middot; click buttons to filter</div>

<script>
const DATA = {data_json};

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

  document.querySelectorAll('.filter-btn').forEach(btn => {{
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
  document.querySelectorAll('.filter-btn').forEach(btn => {{
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

init();
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
    html = build_html(data)

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
