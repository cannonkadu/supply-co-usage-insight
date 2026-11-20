"""Zero-dependency interactive Web Dashboard for Supply Co-usage Insight."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from app.core import run_full_pipeline

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Supply Co-usage Insight — Hospital Procurement Analytics</title>
  <style>
    :root {
      --bg: #0b1020;
      --surface: #121a2f;
      --surface-2: #18223d;
      --border: #253358;
      --text: #e8eefc;
      --muted: #93a4c7;
      --accent: #7c5cff;
      --accent-2: #2dd4bf;
      --warn: #f59e0b;
      --good: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: radial-gradient(circle at top right, #162447 0%, var(--bg) 55%);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.5;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 28px 20px 60px; }
    header {
      display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
      gap: 16px; margin-bottom: 24px; padding-bottom: 18px; border-bottom: 1px solid var(--border);
    }
    .brand h1 { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; }
    .brand p { color: var(--muted); font-size: 0.95rem; margin-top: 4px; }
    .badges { display: flex; gap: 8px; flex-wrap: wrap; }
    .badge {
      padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
      background: var(--surface-2); border: 1px solid var(--border); color: var(--muted);
    }
    .badge.primary { background: rgba(124,92,255,0.2); border-color: var(--accent); color: #c4b5fd; }
    .controls {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 14px; background: var(--surface); border: 1px solid var(--border);
      border-radius: 14px; padding: 16px; margin-bottom: 22px; align-items: end;
    }
    .field label { display: block; font-size: 0.78rem; color: var(--muted); margin-bottom: 6px; font-weight: 600; }
    .field input {
      width: 100%; padding: 9px 12px; border-radius: 8px; border: 1px solid var(--border);
      background: var(--bg); color: var(--text); font-size: 0.92rem;
    }
    .btn {
      padding: 10px 16px; border-radius: 8px; border: none; cursor: pointer;
      font-weight: 600; font-size: 0.9rem; transition: opacity 0.15s;
    }
    .btn:hover { opacity: 0.9; }
    .btn-primary { background: linear-gradient(135deg, var(--accent), #5b3df5); color: white; }
    .btn-ghost { background: var(--surface-2); color: var(--text); border: 1px solid var(--border); }
    .kpis {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px; margin-bottom: 22px;
    }
    .kpi {
      background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 18px;
    }
    .kpi .label { font-size: 0.78rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi .value { font-size: 1.8rem; font-weight: 700; margin-top: 6px; color: var(--accent-2); }
    .kpi .sub { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
    .card {
      background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
      padding: 20px; margin-bottom: 22px; overflow-x: auto;
    }
    .card-header {
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
      gap: 10px; margin-bottom: 14px;
    }
    .card h2 { font-size: 1.15rem; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th, td { text-align: left; padding: 11px 10px; border-bottom: 1px solid var(--border); }
    th { color: var(--muted); font-weight: 600; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; }
    tr:hover td { background: rgba(124,92,255,0.06); }
    .sku-pill {
      display: inline-block; padding: 2px 8px; margin: 2px 4px 2px 0; border-radius: 6px;
      background: var(--surface-2); border: 1px solid var(--border); font-family: monospace; font-size: 0.78rem;
    }
    .lift-strong { color: var(--good); font-weight: 700; }
    .lift-mod { color: var(--warn); font-weight: 700; }
    .lift-base { color: var(--muted); }
    .bar-wrap { width: 110px; height: 8px; background: var(--bg); border-radius: 99px; overflow: hidden; margin-top: 4px; }
    .bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }
    .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 18px; }
    .dept-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>Supply Co-usage Insight</h1>
        <p>Medical supply co-occurrence mining for hospital stock placement &amp; procurement efficiency</p>
      </div>
      <div class="badges">
        <span class="badge primary">Healthcare</span>
        <span class="badge">thilimarketbasket</span>
        <span class="badge">Runs Locally</span>
      </div>
    </header>

    <div class="controls">
      <div class="field">
        <label for="nProcs">Procedures</label>
        <input id="nProcs" type="number" min="50" max="2000" step="50" value="200" />
      </div>
      <div class="field">
        <label for="minSup">Min Support (0.05 - 0.50)</label>
        <input id="minSup" type="number" min="0.05" max="0.50" step="0.01" value="0.10" />
      </div>
      <div class="field">
        <label for="maxSize">Max Bundle Size</label>
        <input id="maxSize" type="number" min="2" max="5" step="1" value="4" />
      </div>
      <div class="field">
        <label for="topN">Top Bundles</label>
        <input id="topN" type="number" min="5" max="50" step="5" value="15" />
      </div>
      <div class="field" style="display:flex; gap:8px;">
        <button class="btn btn-primary" onclick="loadData()" style="flex:1;">Run Analysis</button>
        <button class="btn btn-ghost" onclick="downloadJSON()">Export JSON</button>
      </div>
    </div>

    <div class="kpis" id="kpis"></div>

    <div class="card">
      <div class="card-header">
        <h2>Identified Medical Supply Bundles (vs. Independence Baseline)</h2>
        <span class="badge" id="bundleCountBadge">Loading...</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Supply Bundle (SKUs &amp; Names)</th>
            <th>Observed Support</th>
            <th>Baseline</th>
            <th>Lift</th>
            <th>Est. Cost</th>
            <th>Procurement / Stock Action</th>
          </tr>
        </thead>
        <tbody id="bundlesBody"></tbody>
      </table>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header"><h2>Top Association Rules</h2></div>
        <table>
          <thead><tr><th>If Procedure Uses</th><th>Also Needs</th><th>Conf.</th><th>Lift</th></tr></thead>
          <tbody id="rulesBody"></tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-header"><h2>Procedures by Department</h2></div>
        <div id="deptList"></div>
      </div>
    </div>
  </div>

  <script>
    let latestData = null;

    async function loadData() {
      const n = document.getElementById('nProcs').value;
      const s = document.getElementById('minSup').value;
      const m = document.getElementById('maxSize').value;
      const t = document.getElementById('topN').value;
      const res = await fetch(`/api/analyze?n_procedures=${n}&min_support=${s}&max_size=${m}&top_n=${t}`);
      const data = await res.json();
      latestData = data;
      render(data);
    }

    function render(data) {
      const sum = data.summary;
      const topLift = data.bundles.length ? Math.max(...data.bundles.map(b => b.lift)).toFixed(2) + 'x' : '—';
      document.getElementById('kpis').innerHTML = `
        <div class="kpi"><div class="label">Procedures Analyzed</div><div class="value">${sum.total_procedures}</div><div class="sub">Across ${Object.keys(data.departments).length} hospital departments</div></div>
        <div class="kpi"><div class="label">Unique Supply SKUs</div><div class="value">${sum.unique_skus}</div><div class="sub">${sum.frequent_itemsets_total} frequent itemsets mined</div></div>
        <div class="kpi"><div class="label">Strong Bundles</div><div class="value">${sum.strong_bundles}</div><div class="sub">Lift &ge; 2.0x above baseline</div></div>
        <div class="kpi"><div class="label">Peak Co-usage Lift</div><div class="value">${topLift}</div><div class="sub">vs. naive independence</div></div>
      `;

      document.getElementById('bundleCountBadge').textContent = `${data.bundles.length} bundles shown`;
      document.getElementById('bundlesBody').innerHTML = data.bundles.map((b, i) => {
        const cls = b.lift >= 2.0 ? 'lift-strong' : (b.lift >= 1.25 ? 'lift-mod' : 'lift-base');
        const pills = b.skus.map(sku => `<span class="sku-pill">${sku}</span>`).join('');
        const names = b.names.join(' + ');
        return `
          <tr>
            <td>${i + 1}</td>
            <td><div>${pills}</div><div style="color:var(--muted);font-size:0.78rem;margin-top:3px;">${names}</div></td>
            <td>
              <strong>${(b.support * 100).toFixed(1)}%</strong> <span style="color:var(--muted);font-size:0.78rem;">(${b.procedure_count})</span>
              <div class="bar-wrap"><div class="bar-fill" style="width:${Math.min(100, b.support * 100)}%"></div></div>
            </td>
            <td>${(b.expected_support * 100).toFixed(1)}%</td>
            <td class="${cls}">${b.lift.toFixed(2)}x</td>
            <td>$${b.bundle_unit_cost.toFixed(2)}</td>
            <td style="font-size:0.82rem;">${b.recommendation}</td>
          </tr>
        `;
      }).join('');

      document.getElementById('rulesBody').innerHTML = data.rules.slice(0, 10).map(r => `
        <tr>
          <td>${r.antecedent.map(s => `<span class="sku-pill">${s}</span>`).join('')}</td>
          <td>${r.consequent.map(s => `<span class="sku-pill">${s}</span>`).join('')}</td>
          <td>${(r.confidence * 100).toFixed(0)}%</td>
          <td class="lift-strong">${r.lift.toFixed(2)}x</td>
        </tr>
      `).join('');

      document.getElementById('deptList').innerHTML = Object.entries(data.departments)
        .sort((a, b) => b[1] - a[1])
        .map(([dept, count]) => `
          <div class="dept-row">
            <span>${dept}</span>
            <strong>${count} procedures (${((count / sum.total_procedures) * 100).toFixed(1)}%)</strong>
          </div>
        `).join('');
    }

    function downloadJSON() {
      if (!latestData) return;
      const blob = new Blob([JSON.stringify(latestData, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'supply-co-usage-report.json';
      a.click();
    }

    loadData();
  </script>
</body>
</html>
"""


def _make_handler():
    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/analyze":
                qs = parse_qs(parsed.query)
                n_procedures = int(qs.get("n_procedures", ["200"])[0])
                min_support = float(qs.get("min_support", ["0.10"])[0])
                max_size = int(qs.get("max_size", ["4"])[0])
                top_n = int(qs.get("top_n", ["15"])[0])
                payload = run_full_pipeline(
                    n_procedures=n_procedures,
                    min_support=min_support,
                    max_size=max_size,
                    top_n=top_n,
                )
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return  # keep CLI output clean

    return DashboardHandler


def serve_dashboard(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the local Supply Co-usage Insight web dashboard."""
    server = HTTPServer((host, port), _make_handler())
    print(f"Supply Co-usage Insight dashboard running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard.")
    finally:
        server.server_close()
