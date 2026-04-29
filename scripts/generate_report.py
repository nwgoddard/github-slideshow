#!/usr/bin/env python3
"""Generate a standalone HTML report from realtyrates.com survey JSON data."""

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "_data", "realtyrates")
REPORT_PATH = os.path.join(REPO_ROOT, "report", "index.html")


def load_json(filename: str) -> dict | list:
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path) as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"  Warning: could not load {filename}: {exc}", file=sys.stderr)
        return {}


def fmt_pct(val: float | None, decimals: int = 2) -> str:
    if val is None:
        return "—"
    return f"{val:.{decimals}f}%"


def fmt_range(lo: float | None, hi: float | None, unit: str = "%") -> str:
    if lo is None and hi is None:
        return "—"
    if lo == hi or hi is None:
        return f"{lo:.2f}{unit}"
    return f"{lo:.2f}–{hi:.2f}{unit}"


def build_html(commercial: dict, indices: dict, developer: dict, metadata: dict, history: list) -> str:
    last_updated = metadata.get("last_updated", "unknown")
    try:
        dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        last_updated_fmt = dt.strftime("%B %d, %Y")
    except Exception:
        last_updated_fmt = last_updated

    quarter = commercial.get("quarter") or developer.get("quarter") or "Latest"
    is_stub = metadata.get("is_stub", False)
    stub_banner = (
        '<div class="stub-banner">⚠ Stub / sample data — run <code>scripts/fetch_realtyrates.py</code> to populate with live data</div>'
        if is_stub
        else ""
    )

    # ---- Commercial rates table rows ----------------------------------------
    cap_rows = ""
    property_types = commercial.get("property_types", [])
    for pt in property_types:
        cap_rows += f"""
        <tr>
          <td>{pt['name']}</td>
          <td class="num">{fmt_range(pt.get('cap_rate_low'), pt.get('cap_rate_high'))}</td>
          <td class="num highlight">{fmt_pct(pt.get('cap_rate_avg'))}</td>
          <td class="num">{fmt_range(pt.get('interest_rate_low'), pt.get('interest_rate_high'))}</td>
          <td class="num highlight">{fmt_pct(pt.get('interest_rate_avg'))}</td>
          <td class="num">{fmt_pct(pt.get('ltv_max'), 0) if pt.get('ltv_max') else '—'}</td>
          <td class="num">{int(pt['amortization']) if pt.get('amortization') else '—'} yr</td>
        </tr>"""

    # ---- Indices table rows --------------------------------------------------
    idx_rows = ""
    categories_seen: set[str] = set()
    for idx in indices.get("indices", []):
        cat = idx.get("category", "")
        cat_label = f'<span class="badge">{cat}</span>' if cat else ""
        idx_rows += f"""
        <tr>
          <td>{idx['name']} {cat_label}</td>
          <td class="num highlight">{fmt_pct(idx.get('value'))}</td>
          <td class="muted">{idx.get('note', '')}</td>
        </tr>"""

    # ---- Developer survey sections ------------------------------------------
    dev_sections = ""
    for cat in developer.get("categories", []):
        metric_rows = ""
        for m in cat.get("metrics", []):
            unit = m.get("unit", "%")
            unit_sym = "%" if unit == "%" else f" {unit}"
            metric_rows += f"""
            <tr>
              <td>{m['name']}</td>
              <td class="num">{fmt_range(m.get('low'), m.get('high'), unit_sym)}</td>
              <td class="num highlight">{m.get('avg', '—'):.2f}{unit_sym} avg</td>
            </tr>"""
        dev_sections += f"""
        <div class="dev-category">
          <h3>{cat['name']}</h3>
          <p class="desc">{cat.get('description', '')}</p>
          <table>
            <thead><tr><th>Metric</th><th>Range</th><th>Average</th></tr></thead>
            <tbody>{metric_rows}</tbody>
          </table>
        </div>"""

    # ---- Chart data ----------------------------------------------------------
    chart_labels = json.dumps([pt["name"] for pt in property_types])
    chart_cap_avgs = json.dumps([pt.get("cap_rate_avg") for pt in property_types])
    chart_rate_avgs = json.dumps([pt.get("interest_rate_avg") for pt in property_types])
    chart_indices_labels = json.dumps([i["name"] for i in indices.get("indices", [])])
    chart_indices_vals = json.dumps([i.get("value") for i in indices.get("indices", [])])

    # History chart data
    hist_labels = json.dumps([h.get("fetched_at", "")[:10] for h in history])
    # Focus on apartments as a proxy for market trend
    apt_series: list[float | None] = []
    for h in history:
        pts = h.get("surveys", {}).get("commercial_rates", {}).get("property_types", [])
        apt = next((p for p in pts if "Garden" in p.get("name", "")), None)
        apt_series.append(apt.get("cap_rate_avg") if apt else None)
    hist_data = json.dumps(apt_series)

    # ---- Subdivision highlight stats ----------------------------------------
    sub_cat = next(
        (c for c in developer.get("categories", []) if "Subdivision" in c.get("name", "")),
        {},
    )
    sub_land_rate = next(
        (m for m in sub_cat.get("metrics", []) if "Land" in m.get("name", "") and "Rate" in m.get("name", "")),
        {},
    )
    sub_ltv = next(
        (m for m in sub_cat.get("metrics", []) if "LTV" in m.get("name", "") and "Land" in m.get("name", "")),
        {},
    )
    sub_absorption = next(
        (m for m in sub_cat.get("metrics", []) if "Absorption" in m.get("name", "")),
        {},
    )

    stat_cards = f"""
      <div class="stat-card">
        <div class="stat-label">Subdivision Land Loan Rate</div>
        <div class="stat-value">{fmt_range(sub_land_rate.get('low'), sub_land_rate.get('high'))}</div>
        <div class="stat-sub">Avg {fmt_pct(sub_land_rate.get('avg'))}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Max LTV (Land)</div>
        <div class="stat-value">{fmt_range(sub_ltv.get('low'), sub_ltv.get('high'))}</div>
        <div class="stat-sub">Avg {fmt_pct(sub_ltv.get('avg'))}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Absorption Rate</div>
        <div class="stat-value">{fmt_range(sub_absorption.get('low'), sub_absorption.get('high'), ' lots/mo')}</div>
        <div class="stat-sub">Avg {sub_absorption.get('avg', '—')} lots/month</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">10-Yr Treasury</div>
        <div class="stat-value">{fmt_pct(next((i.get('value') for i in indices.get('indices', []) if '10-Year' in i.get('name','')), None))}</div>
        <div class="stat-sub">Benchmark rate</div>
      </div>"""

    hist_chart_block = ""
    hist_chart_script = ""
    if history:
        hist_chart_block = """
      <section id="history">
        <h2>Historical Cap Rate Trend</h2>
        <p class="subtitle">Apartments (Garden/Low Rise) — quarterly average cap rate</p>
        <div class="chart-container">
          <canvas id="histChart"></canvas>
        </div>
      </section>"""
        hist_chart_script = f"""
    const histLabels = {hist_labels};
    const histData   = {hist_data};
    new Chart(document.getElementById('histChart'), {{
      type: 'line',
      data: {{
        labels: histLabels,
        datasets: [{{
          label: 'Avg Cap Rate — Apts Garden/Low Rise (%)',
          data: histData,
          borderColor: PALETTE_BLUE,
          backgroundColor: 'rgba(79,142,247,0.15)',
          fill: true,
          tension: 0.3,
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ y: {{ title: {{ display: true, text: 'Cap Rate (%)' }} }} }}
      }}
    }});"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Subdivision Analysis — RealtyRates.com Survey Data</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f1117;
      --surface: #1a1d27;
      --border: #2a2d3a;
      --accent: #4f8ef7;
      --accent2: #f76f4f;
      --text: #e2e8f0;
      --muted: #8892a4;
      --green: #4caf7d;
      --yellow: #f5c842;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; }}
    a {{ color: var(--accent); }}
    header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 2rem; text-align: center; }}
    header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: .4rem; }}
    header .meta {{ color: var(--muted); font-size: .9rem; }}
    .stub-banner {{ background: #3a2a00; color: var(--yellow); padding: .75rem 1.5rem; text-align: center; font-size: .9rem; }}
    .stub-banner code {{ background: rgba(255,255,255,.1); padding: 0 .4rem; border-radius: 3px; }}
    nav {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: .75rem 2rem; display: flex; gap: 1.5rem; flex-wrap: wrap; }}
    nav a {{ color: var(--muted); text-decoration: none; font-size: .9rem; }}
    nav a:hover {{ color: var(--text); }}
    main {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
    section {{ margin-bottom: 3rem; }}
    h2 {{ font-size: 1.4rem; font-weight: 600; margin-bottom: .3rem; padding-bottom: .5rem; border-bottom: 1px solid var(--border); }}
    h3 {{ font-size: 1.1rem; font-weight: 600; margin-bottom: .5rem; color: var(--accent); }}
    .subtitle {{ color: var(--muted); font-size: .85rem; margin-bottom: 1.2rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; }}
    .stat-label {{ color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; margin-bottom: .4rem; }}
    .stat-value {{ font-size: 1.6rem; font-weight: 700; color: var(--accent); }}
    .stat-sub {{ color: var(--muted); font-size: .82rem; margin-top: .2rem; }}
    .chart-container {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; font-size: .88rem; }}
    thead th {{ background: #212435; color: var(--muted); font-weight: 600; text-align: left; padding: .7rem 1rem; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; }}
    tbody tr {{ border-top: 1px solid var(--border); }}
    tbody tr:hover {{ background: rgba(79,142,247,.05); }}
    td {{ padding: .65rem 1rem; vertical-align: middle; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    td.highlight {{ color: var(--accent); font-weight: 600; }}
    td.muted {{ color: var(--muted); font-size: .82rem; }}
    .badge {{ background: var(--border); color: var(--muted); font-size: .72rem; padding: .15rem .5rem; border-radius: 20px; margin-left: .4rem; }}
    .dev-category {{ margin-bottom: 2rem; }}
    .dev-category .desc {{ color: var(--muted); font-size: .85rem; margin-bottom: .8rem; }}
    footer {{ background: var(--surface); border-top: 1px solid var(--border); padding: 1.5rem 2rem; text-align: center; color: var(--muted); font-size: .82rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Subdivision Analysis</h1>
    <div class="meta">
      Source: <a href="https://www.realtyrates.com" target="_blank">RealtyRates.com</a> Free Survey Data &nbsp;·&nbsp;
      Survey Period: {quarter} &nbsp;·&nbsp;
      Updated: {last_updated_fmt}
    </div>
  </header>
  {stub_banner}
  <nav>
    <a href="#summary">Summary</a>
    <a href="#cap-rates">Cap Rates</a>
    <a href="#developer-survey">Developer Survey</a>
    <a href="#indices">Financial Indices</a>
    {"<a href='#history'>Historical Trends</a>" if history else ""}
  </nav>
  <main>
    <section id="summary">
      <h2>Subdivision Market Summary</h2>
      <p class="subtitle">{quarter} key metrics from RealtyRates.com survey data</p>
      <div class="stats-grid">
        {stat_cards}
      </div>
    </section>

    <section id="cap-rates">
      <h2>Commercial Cap Rates &amp; Mortgage Rates by Property Type</h2>
      <p class="subtitle">All rates in percent (%). LTV = maximum loan-to-value. Source: RealtyRates.com Commercial Mortgage Rate Survey.</p>
      <div class="chart-container">
        <canvas id="capRateChart" height="120"></canvas>
      </div>
      <table>
        <thead>
          <tr>
            <th>Property Type</th>
            <th style="text-align:right">Cap Rate Range</th>
            <th style="text-align:right">Cap Avg</th>
            <th style="text-align:right">Interest Rate Range</th>
            <th style="text-align:right">Rate Avg</th>
            <th style="text-align:right">Max LTV</th>
            <th style="text-align:right">Amort.</th>
          </tr>
        </thead>
        <tbody>{cap_rows}</tbody>
      </table>
    </section>

    <section id="developer-survey">
      <h2>Developer Survey — Subdivision &amp; Development Financing</h2>
      <p class="subtitle">Financing terms for residential and commercial development projects. Source: RealtyRates.com Developer Survey.</p>
      <div class="chart-container">
        <canvas id="devChart" height="100"></canvas>
      </div>
      {dev_sections}
    </section>

    <section id="indices">
      <h2>Financial Indices &amp; Benchmark Rates</h2>
      <p class="subtitle">Key market reference rates. Source: RealtyRates.com Financial Indices.</p>
      <div class="chart-container">
        <canvas id="idxChart" height="80"></canvas>
      </div>
      <table>
        <thead>
          <tr><th>Index</th><th style="text-align:right">Current Rate</th><th>Notes</th></tr>
        </thead>
        <tbody>{idx_rows}</tbody>
      </table>
    </section>

    {hist_chart_block}
  </main>
  <footer>
    Data sourced from <a href="https://www.realtyrates.com" target="_blank">RealtyRates.com</a> free survey publications.
    Updated {last_updated_fmt}. For informational purposes only.
  </footer>

  <script>
    const PALETTE_BLUE = 'rgba(79,142,247,0.85)';
    const PALETTE_ORANGE = 'rgba(247,111,79,0.85)';
    const PALETTE_GREEN = 'rgba(76,175,125,0.85)';
    const GRID_COLOR = 'rgba(255,255,255,0.06)';
    const TEXT_COLOR = '#8892a4';
    Chart.defaults.color = TEXT_COLOR;
    Chart.defaults.borderColor = GRID_COLOR;

    const capLabels = {chart_labels};
    const capAvgs   = {chart_cap_avgs};
    const rateAvgs  = {chart_rate_avgs};

    new Chart(document.getElementById('capRateChart'), {{
      type: 'bar',
      data: {{
        labels: capLabels,
        datasets: [
          {{ label: 'Avg Cap Rate (%)', data: capAvgs, backgroundColor: PALETTE_BLUE }},
          {{ label: 'Avg Interest Rate (%)', data: rateAvgs, backgroundColor: PALETTE_ORANGE }},
        ]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{
          x: {{ ticks: {{ maxRotation: 45 }} }},
          y: {{ title: {{ display: true, text: 'Rate (%)' }}, min: 0 }}
        }}
      }}
    }});

    // Developer survey chart — land loan rates per category
    const devCategories = {json.dumps([c['name'] for c in developer.get('categories', [])])};
    const devLandRates = {json.dumps([
        next((m.get('avg') for m in c.get('metrics', []) if 'Land' in m.get('name','') and 'Rate' in m.get('name','')), None)
        for c in developer.get('categories', [])
    ])};
    const devConstRates = {json.dumps([
        next((m.get('avg') for m in c.get('metrics', []) if 'Construction' in m.get('name','') and 'Rate' in m.get('name','')), None)
        for c in developer.get('categories', [])
    ])};

    new Chart(document.getElementById('devChart'), {{
      type: 'bar',
      data: {{
        labels: devCategories,
        datasets: [
          {{ label: 'Land Loan Rate Avg (%)', data: devLandRates, backgroundColor: PALETTE_BLUE }},
          {{ label: 'Construction Loan Rate Avg (%)', data: devConstRates, backgroundColor: PALETTE_GREEN }},
        ]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ y: {{ title: {{ display: true, text: 'Rate (%)' }}, min: 0 }} }}
      }}
    }});

    // Indices chart
    const idxLabels = {chart_indices_labels};
    const idxVals   = {chart_indices_vals};
    new Chart(document.getElementById('idxChart'), {{
      type: 'bar',
      indexAxis: 'y',
      data: {{
        labels: idxLabels,
        datasets: [{{ label: 'Rate (%)', data: idxVals, backgroundColor: PALETTE_BLUE }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{ x: {{ title: {{ display: true, text: 'Rate (%)' }}, min: 0 }} }}
      }}
    }});

    {hist_chart_script}
  </script>
</body>
</html>"""


def main() -> int:
    print("Loading survey data…")
    commercial = load_json("commercial_rates.json")
    indices_data = load_json("indices.json")
    developer = load_json("developer_survey.json")
    metadata = load_json("metadata.json")
    history = load_json("history.json")
    if not isinstance(history, list):
        history = []

    print("Generating report…")
    html = build_html(commercial, indices_data, developer, metadata, history)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as fh:
        fh.write(html)
    print(f"Report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
