"""
generate_html.py
================
Run this script once to produce a fully self-contained dashboard.html
that higher-ups can open by double-clicking — no Python, no server, no
internet connection needed on their machine. Plotly.js is downloaded
once here and embedded directly into the HTML file.

Usage:
    python generate_html.py

Output:
    dashboard.html  (in the same folder)

Requirements:
    pip install polars pyarrow requests
"""

import json
import calendar
import urllib.request
from pathlib import Path

import polars as pl

# ── Plotly download ───────────────────────────────────────────────────────────
PLOTLY_URL = "https://cdn.plot.ly/plotly-2.32.0.min.js"
PLOTLY_CACHE = Path(__file__).resolve().parent / ".plotly.min.js.cache"

def fetch_plotly_js() -> str:
    """Download Plotly.js once, cache it locally, return the JS source."""
    if PLOTLY_CACHE.exists():
        print("  → Using cached Plotly.js")
        return PLOTLY_CACHE.read_text(encoding="utf-8")

    print(f"  → Downloading Plotly.js from {PLOTLY_URL} ...")
    with urllib.request.urlopen(PLOTLY_URL, timeout=60) as resp:
        js = resp.read().decode("utf-8")
    PLOTLY_CACHE.write_text(js, encoding="utf-8")
    print(f"  → Cached to {PLOTLY_CACHE.name} ({len(js)//1024} KB)")
    return js

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ALERT_HEADER_PATH  = BASE_DIR / "mock_alert_header.parquet"
WORKFLOW_STATUSES_PATH = BASE_DIR / "mock_workflow_statuses.parquet"
ODD_EXCLUDED_DOMAIN = "SUSPICIOUS ACTIVITY"
OUTPUT_PATH = BASE_DIR / "dashboard.html"

# ── Data loading (mirrors your DeticaParquetAlertRepository) ──────────────────
def load_data() -> pl.DataFrame:
    ah = pl.read_parquet(ALERT_HEADER_PATH)
    ah = ah.rename({c: c.strip() for c in ah.columns})

    ws = pl.read_parquet(WORKFLOW_STATUSES_PATH)
    ws = ws.rename({c: c.strip() for c in ws.columns})

    # Filter excluded domain
    ah = ah.filter(
        pl.col("WW_DOMAIN_CODE").cast(pl.Utf8).str.strip_chars() != ODD_EXCLUDED_DOMAIN
    )

    # Join status name
    df = ah.join(ws.select(["ID", "NAME"]), left_on="WW_STATUS_ID", right_on="ID", how="left")

    # Parse timestamp
    dtype = df.schema.get("WW_CREATION_TIMESTAMP")
    if dtype == pl.Date:
        ts_expr = pl.col("WW_CREATION_TIMESTAMP").cast(pl.Datetime)
    elif isinstance(dtype, pl.Datetime):
        ts_expr = pl.col("WW_CREATION_TIMESTAMP")
    else:
        ts_expr = (
            pl.col("WW_CREATION_TIMESTAMP")
            .cast(pl.Utf8).str.strip_chars()
            .str.strptime(pl.Datetime, strict=False)
        )

    df = (
        df.with_columns([
            pl.col("NAME").cast(pl.Utf8).str.strip_chars(),
            ts_expr.alias("creation_ts"),
        ])
        .filter(pl.col("creation_ts").is_not_null())
        .with_columns([
            pl.col("creation_ts").dt.year().alias("year_creation"),
            pl.col("creation_ts").dt.month().alias("mth_creation"),
            pl.col("creation_ts").dt.date().alias("dt_creation"),
        ])
        .group_by(["year_creation", "mth_creation", "dt_creation", "NAME"])
        .agg(pl.len().alias("Count"))
        .sort(["NAME", "year_creation", "mth_creation", "dt_creation"])
        .select(["year_creation", "mth_creation", "dt_creation", "NAME", "Count"])
    )
    return df


# ── Pre-compute payload ────────────────────────────────────────────────────────
def build_payload(df: pl.DataFrame) -> dict:
    pdf = df.to_pandas()

    # All status names
    names = sorted(pdf["NAME"].dropna().unique().tolist())

    # All years
    years = sorted(pdf["year_creation"].dropna().unique().astype(int).tolist())

    # All months (number → name)
    month_nums = sorted(pdf["mth_creation"].dropna().unique().astype(int).tolist())
    months = [{"value": m, "label": calendar.month_name[m]} for m in month_nums]

    # Raw aggregated rows for JS to filter client-side
    # Columns: NAME, year_creation, mth_creation, dt_creation (as string), Count
    rows = []
    for _, r in pdf.iterrows():
        rows.append({
            "n": str(r["NAME"]),
            "y": int(r["year_creation"]),
            "m": int(r["mth_creation"]),
            "d": str(r["dt_creation"]),
            "c": int(r["Count"]),
        })

    return {
        "names": names,
        "years": years,
        "months": months,
        "rows": rows,
    }


# ── HTML template ──────────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ODD Alerts Dashboard</title>
<script>__PLOTLY_JS__</script>
<style>
/* ── Reset ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:#1f2937}

/* ── Shell ── */
.shell{display:flex;min-height:100vh}

/* ── Sidebar ── */
.sidebar{background:linear-gradient(180deg,#8A0303 0%,#610000 100%);color:#fff;width:260px;min-width:260px;padding:20px 16px;display:flex;flex-direction:column;gap:18px;position:fixed;top:0;left:0;height:100vh;overflow:hidden;transition:width .25s ease;z-index:1000;box-shadow:4px 0 15px rgba(0,0,0,.08)}
.sidebar.collapsed{width:68px;min-width:68px}
.sidebar-brand{display:flex;align-items:center;gap:14px}
.brand-text{overflow:hidden;white-space:nowrap}
.brand-title{font-weight:800;font-size:17px}
.brand-subtitle{font-size:11px;color:rgba(255,255,255,.7);margin-top:2px}
.toggle-btn{width:38px;height:38px;border-radius:8px;border:none;background:rgba(255,255,255,.1);color:#fff;cursor:pointer;font-size:19px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .2s}
.toggle-btn:hover{background:rgba(255,255,255,.2)}
.sidebar-section-label{font-size:10px;font-weight:700;letter-spacing:1.2px;color:rgba(255,255,255,.45);text-transform:uppercase;margin-top:4px}
.sidebar.collapsed .sidebar-section-label,.sidebar.collapsed .brand-text,.sidebar.collapsed .nav-text,.sidebar.collapsed .sidebar-info-card{display:none}
.sidebar-nav{display:flex;flex-direction:column;gap:6px}
.nav-link{text-decoration:none;color:rgba(255,255,255,.8);padding:12px 14px;border-radius:0 10px 10px 0;font-weight:600;font-size:13px;display:flex;align-items:center;gap:12px;border-left:4px solid transparent;transition:all .2s;white-space:nowrap;overflow:hidden}
.nav-link.active{background:rgba(255,255,255,.12);border-left:4px solid #FFC220;color:#fff}
.nav-link:hover:not(.active){background:rgba(255,255,255,.06);color:#fff}
.sidebar.collapsed .nav-link{justify-content:center;border-left:none;padding:12px}
.sidebar.collapsed .nav-link.active{background:rgba(255,255,255,.15);border-left:none}
.nav-icon{width:20px;height:20px;background:currentColor;display:inline-block;flex-shrink:0}
.icon-home{-webkit-mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>') no-repeat center/contain;mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>') no-repeat center/contain}
.icon-search{-webkit-mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>') no-repeat center/contain;mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>') no-repeat center/contain}
.sidebar-info-card{margin-top:auto;background:rgba(0,0,0,.2);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:14px}
.sidebar-info-title{font-weight:800;font-size:12px;margin-bottom:10px;color:#FFC220;text-transform:uppercase;letter-spacing:.5px}
.sidebar-info-list{padding-left:16px;font-size:11px;line-height:1.7;color:rgba(255,255,255,.82)}

/* ── Main ── */
.main{flex:1;margin-left:260px;padding:14px 28px 36px 22px;transition:margin-left .25s ease;min-width:0}
.main.collapsed{margin-left:68px}

/* ── Pages ── */
.page{display:none}.page.active{display:block}

/* ── Hero header ── */
.hero{background:radial-gradient(circle at top right,rgba(255,194,32,.12),transparent 30%),linear-gradient(135deg,#8A0303 0%,#A80519 60%,#B91C1C 100%);border-radius:12px;padding:16px 20px;margin-bottom:18px;border:1px solid rgba(255,255,255,.1);box-shadow:0 10px 22px rgba(138,3,3,.12);overflow:hidden;position:relative}
.hero::before{content:"";position:absolute;inset:0;background:linear-gradient(120deg,rgba(255,255,255,.05),transparent 35%);pointer-events:none}
.hero-badge{display:inline-flex;align-items:center;gap:8px;padding:4px 10px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.16);color:#FFF8E1;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;margin-bottom:8px}
.hero-dot{width:7px;height:7px;border-radius:50%;background:#FFC220;box-shadow:0 0 0 3px rgba(255,194,32,.18);flex-shrink:0}
.hero h1{color:#fff;font-size:20px;font-weight:800;letter-spacing:-.3px;margin-bottom:6px}
.hero p{color:rgba(255,255,255,.82);font-size:12px;line-height:1.5;max-width:700px}

/* ── Filter bar ── */
.filter-bar{background:#fff;border:1px solid #E2E8F0;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,.03);padding:16px 20px;display:grid;grid-template-columns:44px minmax(160px,1.3fr) minmax(130px,.8fr) minmax(130px,.8fr) minmax(260px,1.1fr);gap:14px;align-items:end;margin-bottom:20px}
.filter-label{display:block;font-size:11px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.filter-group{display:flex;flex-direction:column;min-width:0}
.reset-btn{width:44px;height:44px;border-radius:10px;border:1px solid #FECDD3;background:#FFF1F2;color:#A80519;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;align-self:end;flex-shrink:0}
.reset-btn:hover{background:#FEE2E2;transform:translateY(-1px);box-shadow:0 6px 14px rgba(168,5,25,.1)}
.reset-icon{width:16px;height:16px;background:currentColor;-webkit-mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v6h6"/><path d="M21 12A9 9 0 0 0 6 5.3L3 8"/><path d="M21 22v-6h-6"/><path d="M3 12a9 9 0 0 0 15 6.7L21 16"/></svg>') no-repeat center/contain;mask:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M3 2v6h6"/><path d="M21 12A9 9 0 0 0 6 5.3L3 8"/><path d="M21 22v-6h-6"/><path d="M3 12a9 9 0 0 0 15 6.7L21 16"/></svg>') no-repeat center/contain;display:inline-block}

/* Custom multi-select */
.multi-select{position:relative}
.multi-select-box{min-height:44px;border:1px solid #D1D5DB;border-radius:8px;background:#fff;padding:6px 10px;cursor:pointer;display:flex;flex-wrap:wrap;gap:4px;align-items:center;font-size:13px;color:#6B7280;transition:border-color .2s}
.multi-select-box:hover,.multi-select-box.open{border-color:#A80519}
.multi-select-box .placeholder{color:#9CA3AF;font-size:13px;user-select:none}
.tag{background:#FEE2E2;color:#A80519;border-radius:5px;padding:2px 7px;font-size:11px;font-weight:600;display:flex;align-items:center;gap:4px;white-space:nowrap}
.tag-x{cursor:pointer;font-size:13px;line-height:1;color:#A80519;margin-left:2px}
.tag-x:hover{color:#8A0303}
.dropdown-panel{position:absolute;top:calc(100% + 4px);left:0;right:0;background:#fff;border:1px solid #E2E8F0;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.1);z-index:999;max-height:220px;overflow-y:auto;display:none}
.dropdown-panel.open{display:block}
.dropdown-option{padding:10px 14px;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:background .15s}
.dropdown-option:hover{background:#FFF1F2}
.dropdown-option input[type=checkbox]{accent-color:#A80519;width:14px;height:14px;flex-shrink:0}
.dropdown-option.selected{background:#FFF1F2;font-weight:600;color:#A80519}

/* Trend mode toggle */
.trend-toggle{display:flex;gap:8px;min-height:44px;align-items:stretch}
.trend-btn{flex:1;border:1px solid #D1D5DB;background:#F9FAFB;border-radius:8px;font-size:12px;font-weight:600;color:#4B5563;cursor:pointer;padding:0 10px;transition:all .2s;white-space:nowrap}
.trend-btn.active{background:#A80519;color:#fff;border-color:#A80519}
.trend-btn:hover:not(.active){background:#F3F4F6;border-color:#9CA3AF}

/* ── KPI grid ── */
.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(150px,1fr));gap:18px;margin-bottom:22px}
.kpi-card{background:#fff;border:1px solid #E2E8F0;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,.03);padding:20px;display:flex;flex-direction:column;justify-content:space-between;min-height:108px}
.kpi-label{font-size:12px;font-weight:700;color:#4B5563;text-transform:uppercase;letter-spacing:.5px}
.kpi-value{font-size:30px;font-weight:800;margin-top:8px}
.kpi-bar{margin-top:12px;height:5px;border-radius:999px;background:#F3F4F6;overflow:hidden}
.kpi-bar-fill{width:100%;height:100%;opacity:.9}
.kpi-purple .kpi-value{color:#A80519}.kpi-purple .kpi-bar-fill{background:#A80519}
.kpi-blue   .kpi-value{color:#111827}.kpi-blue   .kpi-bar-fill{background:#111827}
.kpi-green  .kpi-value{color:#D97706}.kpi-green  .kpi-bar-fill{background:#FFC220}
.kpi-rose   .kpi-value{color:#8A0303}.kpi-rose   .kpi-bar-fill{background:#8A0303}

/* ── Chart cards ── */
.card{background:#fff;border:1px solid #E2E8F0;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,.03);padding:18px;overflow:hidden}
.card-title{font-size:15px;font-weight:800;color:#111827;margin-bottom:14px;display:flex;align-items:center}
.card-title::before{content:"";display:inline-block;width:4px;height:15px;background:#A80519;margin-right:8px;border-radius:2px}
.trend-grid{display:grid;grid-template-columns:3fr .55fr;gap:18px;align-items:start;margin-bottom:22px}
.double-grid{display:grid;grid-template-columns:.85fr 1fr;gap:20px;align-items:start}
.side-grid{display:grid;grid-template-columns:1.6fr .55fr;gap:14px;align-items:start}
.chart-box{width:100%;height:340px}
.chart-box-large{width:100%;height:340px}
.insight-panel{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:14px;height:340px;overflow-y:auto}
.insight-title{font-weight:800;font-size:12px;margin-bottom:10px;color:#A80519;text-transform:uppercase;letter-spacing:.5px}
.insight-list{padding-left:18px;color:#4B5563;font-size:12px;line-height:1.8}
.insight-list li{margin-bottom:8px}.insight-list li::marker{color:#A80519}
.insight-panel::-webkit-scrollbar{width:5px}.insight-panel::-webkit-scrollbar-track{background:#F3F4F6;border-radius:999px}.insight-panel::-webkit-scrollbar-thumb{background:#D1D5DB;border-radius:999px}

/* ── Explorer ── */
.explorer-card{background:#fff;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.04)}
.explorer-card-header{padding:18px 22px 14px;border-bottom:1px solid #E5E7EB}
.explorer-card-header h2{font-size:17px;color:#111827;font-weight:800}
.explorer-card-header p{margin-top:4px;color:#6B7280;font-size:12px}
.table-header{display:grid;grid-template-columns:1fr 200px;background:linear-gradient(90deg,#A80519,#8A0303);color:#FFC220;font-weight:800;font-size:12px;text-transform:uppercase;letter-spacing:.8px}
.table-header>div,.cell{padding:14px 24px}
.center-col,.cell-count{text-align:center;display:flex;justify-content:center;font-variant-numeric:tabular-nums}
.table-row{display:grid;grid-template-columns:1fr 200px;align-items:center}
.year-row{cursor:pointer;background:#FFF1F2;font-weight:700;font-size:14px;color:#8A0303;border-bottom:2px solid #FECDD3;transition:background .2s}
.year-row:hover{background:#FEE2E2}
.year-row .cell-label{border-left:6px solid #E2001A;padding-left:18px}
.year-row .cell-count{font-size:15px;font-weight:800;color:#8A0303}
.month-row{cursor:pointer;background:#FFFAF0;font-weight:600;color:#92400E;border-bottom:1px solid #FEF3C7;transition:background .2s;font-size:13px}
.month-row:hover{background:#FEF3C7}
.month-row .cell-label{padding-left:44px}
.date-row{cursor:pointer;background:#fff;color:#374151;font-weight:600;border-bottom:1px solid #E5E7EB;transition:background .2s;font-size:13px}
.date-row:hover{background:#F9FAFB}
.date-row .cell-label{padding-left:72px}
.day-row{background:#F3F4F6;color:#4B5563;border-bottom:1px solid #E5E7EB;font-size:12px}
.day-row .cell-label{padding-left:100px;font-weight:500}
.day-row .cell-count{font-size:13px;font-weight:600}
.expand-icon{display:inline-block;width:18px;color:#E2001A;font-size:10px;margin-right:8px;transition:transform .2s}
.sub-container{display:none}
.year-wrapper+.year-wrapper{border-top:8px solid #F4F6F8}

/* Explorer filter */
.explorer-filter{background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:14px 18px;margin-bottom:18px;display:flex;align-items:end;gap:14px}
.explorer-filter .filter-group{max-width:280px}

/* No data */
.no-data{padding:40px;text-align:center;color:#9CA3AF;font-size:14px}

@media(max-width:1200px){.kpi-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:1100px){.double-grid{grid-template-columns:1fr}.side-grid{grid-template-columns:2fr .7fr}}
@media(max-width:900px){.trend-grid,.side-grid{grid-template-columns:1fr}.filter-bar{grid-template-columns:44px 1fr}}
</style>
</head>
<body>
<div class="shell">

<!-- ── Sidebar ── -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <button class="toggle-btn" id="sidebarToggle">☰</button>
    <div class="brand-text">
      <div class="brand-title">ODD Alerts</div>
      <div class="brand-subtitle">Enterprise Monitoring</div>
    </div>
  </div>
  <div class="sidebar-section-label">Navigation</div>
  <nav class="sidebar-nav">
    <a class="nav-link active" id="navDashboard" href="#" onclick="showPage('dashboard');return false">
      <span class="nav-icon icon-home"></span><span class="nav-text">Dashboard Overview</span>
    </a>
    <a class="nav-link" id="navExplorer" href="#" onclick="showPage('explorer');return false">
      <span class="nav-icon icon-search"></span><span class="nav-text">Detail Explorer</span>
    </a>
  </nav>
  <div class="sidebar-info-card">
    <div class="sidebar-info-title">Quick Guide</div>
    <ul class="sidebar-info-list">
      <li>Use filters to isolate specific status types or periods.</li>
      <li>Toggle Trend View to compare individual workflows.</li>
      <li>Navigate to Explorer for daily data drill-down.</li>
    </ul>
  </div>
</aside>

<!-- ── Main ── -->
<main class="main" id="main">

  <!-- ═══════════════ DASHBOARD PAGE ═══════════════ -->
  <div class="page active" id="page-dashboard">
    <div class="hero">
      <div class="hero-badge"><span class="hero-dot"></span><span>Operational Intelligence</span></div>
      <h1>Alerts Monitoring Dashboard</h1>
      <p>Track operational workloads, identify bottlenecks, and monitor long-term trends across workflow statuses, periods, and yearly activity.</p>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <button class="reset-btn" title="Reset filters" onclick="resetFilters()"><span class="reset-icon"></span></button>

      <div class="filter-group">
        <label class="filter-label">Alert Status</label>
        <div class="multi-select" id="ms-status">
          <div class="multi-select-box" id="ms-status-box" onclick="toggleDropdown('ms-status')">
            <span class="placeholder">All statuses</span>
          </div>
          <div class="dropdown-panel" id="ms-status-panel"></div>
        </div>
      </div>

      <div class="filter-group">
        <label class="filter-label">Year</label>
        <div class="multi-select" id="ms-year">
          <div class="multi-select-box" id="ms-year-box" onclick="toggleDropdown('ms-year')">
            <span class="placeholder">All years</span>
          </div>
          <div class="dropdown-panel" id="ms-year-panel"></div>
        </div>
      </div>

      <div class="filter-group">
        <label class="filter-label">Month</label>
        <div class="multi-select" id="ms-month">
          <div class="multi-select-box" id="ms-month-box" onclick="toggleDropdown('ms-month')">
            <span class="placeholder">All months</span>
          </div>
          <div class="dropdown-panel" id="ms-month-panel"></div>
        </div>
      </div>

      <div class="filter-group">
        <label class="filter-label">Trend View Mode</label>
        <div class="trend-toggle">
          <button class="trend-btn active" id="btn-total" onclick="setTrendMode('total')">Total Aggregate</button>
          <button class="trend-btn" id="btn-compare" onclick="setTrendMode('compare')">Status Comparison</button>
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="kpi-grid" id="kpiGrid"></div>

    <!-- Trend chart -->
    <div class="trend-grid card" style="margin-bottom:22px">
      <div>
        <div class="card-title">Monthly Workflow Trend</div>
        <div class="chart-box-large" id="trendChart"></div>
      </div>
      <div>
        <div class="insight-panel">
          <div class="insight-title">Automated Insights</div>
          <ul class="insight-list" id="trendInsights"></ul>
        </div>
      </div>
    </div>

    <!-- Status + Yearly -->
    <div class="double-grid">
      <div class="card">
        <div class="card-title">Status Distribution</div>
        <div class="side-grid">
          <div class="chart-box" id="statusChart"></div>
          <div class="insight-panel">
            <div class="insight-title">Volume Analysis</div>
            <ul class="insight-list" id="statusInsights"></ul>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">Yearly Breakdown</div>
        <div class="side-grid">
          <div class="chart-box" id="yearlyChart"></div>
          <div class="insight-panel">
            <div class="insight-title">Year-over-Year</div>
            <ul class="insight-list" id="yearlyInsights"></ul>
          </div>
        </div>
      </div>
    </div>
  </div><!-- /dashboard page -->

  <!-- ═══════════════ EXPLORER PAGE ═══════════════ -->
  <div class="page" id="page-explorer">
    <div class="hero">
      <div class="hero-badge"><span class="hero-dot"></span><span>Deep Drill-Down Workspace</span></div>
      <h1>Data Detail Explorer</h1>
      <p>Explore alert activity from status level to financial year, monitoring period, and daily volume distribution.</p>
    </div>

    <!-- Explorer status filter -->
    <div class="explorer-filter">
      <div class="filter-group">
        <label class="filter-label">Filter by Status</label>
        <div class="multi-select" id="ms-exp-status">
          <div class="multi-select-box" id="ms-exp-status-box" onclick="toggleDropdown('ms-exp-status')">
            <span class="placeholder">All statuses</span>
          </div>
          <div class="dropdown-panel" id="ms-exp-status-panel"></div>
        </div>
      </div>
      <button class="reset-btn" title="Reset" onclick="resetExplorer()" style="margin-bottom:0;align-self:end"><span class="reset-icon"></span></button>
    </div>

    <div class="explorer-card">
      <div class="explorer-card-header">
        <h2>Available Workflows &amp; Statuses</h2>
        <p>Click on any status row to drill down into historical distributions.</p>
      </div>
      <div class="table-header">
        <div>Hierarchy Classification</div>
        <div class="center-col">Total Occurrences</div>
      </div>
      <div id="explorerList"></div>
    </div>
  </div><!-- /explorer page -->

</main>
</div><!-- /shell -->

<script>
// ══════════════════════════════════════════════════════
//  EMBEDDED DATA  (generated by generate_html.py)
// ══════════════════════════════════════════════════════
const PAYLOAD = __PAYLOAD__;

// ══════════════════════════════════════════════════════
//  COLOURS
// ══════════════════════════════════════════════════════
const PB_RED='#E2001A',PB_DARK_RED='#990012',PB_YELLOW='#FFC220',
      PB_DARK_GREY='#374151',PB_LIGHT_GREY='#9CA3AF';
const COLOR_SEQ=[PB_RED,PB_YELLOW,PB_DARK_GREY,PB_DARK_RED,PB_LIGHT_GREY,'#D1D5DB','#1F2937'];
const PLOTLY_LAYOUT={
  paper_bgcolor:'#ffffff',plot_bgcolor:'#ffffff',
  font:{family:"-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif",color:'#1f2937'},
  margin:{l:55,r:20,t:10,b:50},
  xaxis:{showgrid:true,gridcolor:'#F3F4F6',zeroline:false,linecolor:'#E5E7EB',automargin:true},
  yaxis:{showgrid:true,gridcolor:'#F3F4F6',zeroline:false,linecolor:'#E5E7EB',automargin:true},
  showlegend:false,hovermode:'closest'
};
const PLOTLY_CFG={displaylogo:false,responsive:true};

// ══════════════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════════════
let selStatus=[], selYears=[], selMonths=[], trendMode='total';
let expStatus=[];

// ══════════════════════════════════════════════════════
//  SIDEBAR
// ══════════════════════════════════════════════════════
document.getElementById('sidebarToggle').onclick=function(){
  document.getElementById('sidebar').classList.toggle('collapsed');
  document.getElementById('main').classList.toggle('collapsed');
};

// ══════════════════════════════════════════════════════
//  PAGE ROUTING
// ══════════════════════════════════════════════════════
function showPage(name){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+name).classList.add('active');
  document.querySelectorAll('.nav-link').forEach(l=>l.classList.remove('active'));
  document.getElementById('nav'+name.charAt(0).toUpperCase()+name.slice(1)).classList.add('active');
  if(name==='explorer') renderExplorer();
}

// ══════════════════════════════════════════════════════
//  MULTI-SELECT WIDGET
// ══════════════════════════════════════════════════════
function toggleDropdown(id){
  const panel=document.getElementById(id+'-panel');
  const isOpen=panel.classList.contains('open');
  // close all others
  document.querySelectorAll('.dropdown-panel.open').forEach(p=>p.classList.remove('open'));
  document.querySelectorAll('.multi-select-box.open').forEach(b=>b.classList.remove('open'));
  if(!isOpen){
    panel.classList.add('open');
    document.getElementById(id+'-box').classList.add('open');
  }
}
document.addEventListener('click',function(e){
  if(!e.target.closest('.multi-select')){
    document.querySelectorAll('.dropdown-panel.open').forEach(p=>p.classList.remove('open'));
    document.querySelectorAll('.multi-select-box.open').forEach(b=>b.classList.remove('open'));
  }
});

function buildDropdown(containerId, options, selectedArr, onChange){
  const panel=document.getElementById(containerId+'-panel');
  panel.innerHTML='';
  options.forEach(opt=>{
    const div=document.createElement('div');
    div.className='dropdown-option'+(selectedArr.includes(opt.value)?' selected':'');
    div.innerHTML=`<input type="checkbox" ${selectedArr.includes(opt.value)?'checked':''}/><span>${opt.label}</span>`;
    div.onclick=function(e){
      e.stopPropagation();
      const cb=div.querySelector('input');
      if(selectedArr.includes(opt.value)){
        selectedArr.splice(selectedArr.indexOf(opt.value),1);
        div.classList.remove('selected'); cb.checked=false;
      } else {
        selectedArr.push(opt.value);
        div.classList.add('selected'); cb.checked=true;
      }
      renderTags(containerId, options, selectedArr, onChange);
      onChange();
    };
    panel.appendChild(div);
  });
  renderTags(containerId, options, selectedArr, onChange);
}

function renderTags(containerId, options, selectedArr, onChange){
  const box=document.getElementById(containerId+'-box');
  box.innerHTML='';
  if(selectedArr.length===0){
    box.innerHTML='<span class="placeholder">'+box.dataset.placeholder+'</span>';
    return;
  }
  selectedArr.forEach(val=>{
    const opt=options.find(o=>o.value===val);
    if(!opt) return;
    const tag=document.createElement('span');
    tag.className='tag';
    tag.innerHTML=`${opt.label}<span class="tag-x" data-val="${val}">×</span>`;
    tag.querySelector('.tag-x').onclick=function(e){
      e.stopPropagation();
      selectedArr.splice(selectedArr.indexOf(val),1);
      renderTags(containerId, options, selectedArr, onChange);
      buildDropdown(containerId, options, selectedArr, onChange);
      onChange();
    };
    box.appendChild(tag);
  });
}

// ══════════════════════════════════════════════════════
//  FILTER HELPERS
// ══════════════════════════════════════════════════════
function filteredRows(){
  return PAYLOAD.rows.filter(r=>{
    if(selStatus.length && !selStatus.includes(r.n)) return false;
    if(selYears.length  && !selYears.includes(r.y))  return false;
    if(selMonths.length && !selMonths.includes(r.m))  return false;
    return true;
  });
}

function groupBy(rows, key){
  const map={};
  rows.forEach(r=>{
    const k=r[key];
    map[k]=(map[k]||0)+r.c;
  });
  return map;
}

// ══════════════════════════════════════════════════════
//  KPI
// ══════════════════════════════════════════════════════
function renderKPIs(rows){
  const total=rows.reduce((s,r)=>s+r.c,0);
  const closed=rows.filter(r=>r.n.startsWith('Closed')).reduce((s,r)=>s+r.c,0);
  const open=rows.filter(r=>!r.n.startsWith('Closed')).reduce((s,r)=>s+r.c,0);
  const escalated=rows.filter(r=>r.n==='Escalated').reduce((s,r)=>s+r.c,0);
  const closureRate=total?closed/total*100:0;
  const escalRate=total?escalated/total*100:0;

  const cards=[
    {label:'Total Alerts',value:total.toLocaleString(),cls:'kpi-purple'},
    {label:'Open Alerts',value:open.toLocaleString(),cls:'kpi-blue'},
    {label:'Closure Rate',value:closureRate.toFixed(1)+'%',cls:'kpi-green'},
    {label:'Escalation Rate',value:escalRate.toFixed(1)+'%',cls:'kpi-rose'},
  ];
  const grid=document.getElementById('kpiGrid');
  grid.innerHTML=cards.map(c=>`
    <div class="kpi-card ${c.cls}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-bar"><div class="kpi-bar-fill"></div></div>
    </div>`).join('');
}

// ══════════════════════════════════════════════════════
//  TREND CHART
// ══════════════════════════════════════════════════════
const MONTH_ABR=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function renderTrend(rows){
  const el=document.getElementById('trendChart');
  if(!rows.length){Plotly.purge(el);el.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9CA3AF;font-size:14px">No data available in current filter scope</div>';renderTrendInsights([]);return;}

  if(trendMode==='compare'){
    // group by NAME + period
    const map={};
    rows.forEach(r=>{
      const key=r.y*100+r.m;
      const label=MONTH_ABR[r.m]+' '+r.y;
      if(!map[r.n]) map[r.n]={};
      map[r.n][key]=(map[r.n][key]||{label,count:0});
      map[r.n][key].count+=r.c;
    });
    const allKeys=[...new Set(rows.map(r=>r.y*100+r.m))].sort();
    const traces=Object.entries(map).map(([name,periods],i)=>({
      type:'scatter',mode:'lines+markers',name,
      x:allKeys.map(k=>periods[k]?periods[k].label:MONTH_ABR[k%100]+' '+Math.floor(k/100)),
      y:allKeys.map(k=>periods[k]?periods[k].count:0),
      line:{width:2.5,color:COLOR_SEQ[i%COLOR_SEQ.length]},
      marker:{size:6},
      hovertemplate:'<b>%{fullData.name}</b><br>Period: %{x}<br>Total: %{y:,}<extra></extra>'
    }));
    const layout={...PLOTLY_LAYOUT,showlegend:true,xaxis_title:'Monitoring Period',yaxis_title:'Alert Volume',
      legend:{orientation:'h',yanchor:'bottom',y:1.02,xanchor:'left',x:0,font:{size:11}},
      margin:{l:55,r:20,t:30,b:55}};
    Plotly.react(el,traces,layout,PLOTLY_CFG);
    renderTrendInsights(rows);
  } else {
    const map={};
    rows.forEach(r=>{const k=r.y*100+r.m; map[k]=(map[k]||{label:MONTH_ABR[r.m]+' '+r.y,count:0}); map[k].count+=r.c;});
    const sorted=Object.entries(map).sort((a,b)=>a[0]-b[0]);
    const xs=sorted.map(e=>e[1].label), ys=sorted.map(e=>e[1].count);
    const trace={type:'scatter',mode:'lines+markers',x:xs,y:ys,
      line:{width:3,color:PB_RED},
      marker:{size:8,color:PB_YELLOW,line:{width:1,color:PB_DARK_RED}},
      hovertemplate:'<b>%{x}</b><br>Total: %{y:,}<extra></extra>'};
    const layout={...PLOTLY_LAYOUT,xaxis_title:'Monitoring Period',yaxis_title:'Total Alert Volume',margin:{l:55,r:20,t:10,b:55}};
    Plotly.react(el,[trace],layout,PLOTLY_CFG);
    renderTrendInsights(rows);
  }
}

function renderTrendInsights(rows){
  const ul=document.getElementById('trendInsights');
  if(!rows.length){ul.innerHTML='<li>No trend insight available.</li>';return;}
  const items=[];
  if(trendMode==='compare'){
    const totals={};
    rows.forEach(r=>{totals[r.n]=(totals[r.n]||0)+r.c;});
    const sorted=Object.entries(totals).sort((a,b)=>b[1]-a[1]);
    sorted.slice(0,3).forEach(([name,cnt],i)=>items.push(`Top ${i+1} trend contributor: ${name} accounts for ${cnt.toLocaleString()} alerts in the selected period.`));
    if(sorted.length>1) items.push(`Comparison signal: ${sorted[0][0]} leads the next selected status by ${(sorted[0][1]-sorted[1][1]).toLocaleString()} alerts.`);
  } else {
    const map={};
    rows.forEach(r=>{const k=r.y*100+r.m; map[k]=(map[k]||{label:MONTH_ABR[r.m]+' '+r.y,count:0}); map[k].count+=r.c;});
    const sorted=Object.entries(map).sort((a,b)=>a[0]-b[0]);
    if(!sorted.length) return;
    const peak=sorted.reduce((a,b)=>b[1].count>a[1].count?b:a);
    items.push(`Peak workload period: ${peak[1].label} recorded the highest total with ${peak[1].count.toLocaleString()} alerts.`);
    if(sorted.length>1){
      const diff=sorted[sorted.length-1][1].count-sorted[0][1].count;
      items.push(`Trend direction: alert volume ${diff>=0?'increased':'decreased'} by ${Math.abs(diff).toLocaleString()} from ${sorted[0][1].label} to ${sorted[sorted.length-1][1].label}.`);
      const avg=sorted.reduce((s,e)=>s+e[1].count,0)/sorted.length;
      items.push(`Average monthly workload across the selected period is ${Math.round(avg).toLocaleString()} alerts.`);
    }
  }
  ul.innerHTML=items.map(t=>`<li>${t}</li>`).join('');
}

// ══════════════════════════════════════════════════════
//  STATUS CHART
// ══════════════════════════════════════════════════════
function renderStatus(rows){
  const el=document.getElementById('statusChart');
  if(!rows.length){Plotly.purge(el);el.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9CA3AF;font-size:14px">No data available</div>';renderStatusInsights([]);return;}
  const map=groupBy(rows,'n');
  const sorted=Object.entries(map).sort((a,b)=>b[1]-a[1]);
  const trace={type:'bar',x:sorted.map(e=>e[0]),y:sorted.map(e=>e[1]),marker:{color:PB_RED},hovertemplate:'<b>%{x}</b><br>Total: %{y:,}<extra></extra>'};
  const layout={...PLOTLY_LAYOUT,xaxis:{...PLOTLY_LAYOUT.xaxis,tickangle:-45,automargin:true},xaxis_title:'Alert Status',yaxis_title:'Volume',margin:{l:60,r:20,t:10,b:110}};
  Plotly.react(el,[trace],layout,PLOTLY_CFG);
  renderStatusInsights(rows);
}

function renderStatusInsights(rows){
  const ul=document.getElementById('statusInsights');
  if(!rows.length){ul.innerHTML='<li>No status insight available.</li>';return;}
  const map=groupBy(rows,'n');
  const total=Object.values(map).reduce((s,v)=>s+v,0);
  const sorted=Object.entries(map).sort((a,b)=>b[1]-a[1]);
  const items=sorted.slice(0,3).map(([name,cnt],i)=>`Top ${i+1} status: ${name} contributes ${cnt.toLocaleString()} alerts (${(cnt/total*100).toFixed(1)}% of selected workload).`);
  const closed=rows.filter(r=>r.n.startsWith('Closed')).reduce((s,r)=>s+r.c,0);
  const open=rows.filter(r=>!r.n.startsWith('Closed')).reduce((s,r)=>s+r.c,0);
  items.push(open>closed?'Operational signal: open-stage alerts exceed closed-stage alerts, which may indicate backlog pressure.':'Operational signal: closed-stage alerts remain higher than open-stage alerts, suggesting stronger completion throughput.');
  ul.innerHTML=items.map(t=>`<li>${t}</li>`).join('');
}

// ══════════════════════════════════════════════════════
//  YEARLY CHART
// ══════════════════════════════════════════════════════
function renderYearly(rows){
  const el=document.getElementById('yearlyChart');
  if(!rows.length){Plotly.purge(el);el.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9CA3AF;font-size:14px">No data available</div>';renderYearlyInsights([]);return;}
  const yearTotals={}, yearByName={};
  rows.forEach(r=>{
    const y=String(r.y);
    yearTotals[y]=(yearTotals[y]||0)+r.c;
    if(!yearByName[r.n]) yearByName[r.n]={};
    yearByName[r.n][y]=(yearByName[r.n][y]||0)+r.c;
  });
  const years=Object.keys(yearTotals).sort();
  const names=Object.keys(yearByName).sort();
  const maxTotal=Math.max(...Object.values(yearTotals));
  const traces=names.map((name,i)=>({
    type:'bar',orientation:'h',name,
    y:years,x:years.map(y=>yearByName[name][y]||0),
    marker:{color:COLOR_SEQ[i%COLOR_SEQ.length]},
    hovertemplate:'Year: %{y}<br>Status: %{fullData.name}<br>Total: %{x:,}<extra></extra>'
  }));
  traces.push({
    type:'scatter',mode:'text',showlegend:false,hoverinfo:'skip',
    y:years,x:years.map(y=>yearTotals[y]),
    text:years.map(y=>'  '+yearTotals[y].toLocaleString()),
    textposition:'middle right',textfont:{color:'#111827',size:13}
  });
  const layout={
    barmode:'stack',paper_bgcolor:'#ffffff',plot_bgcolor:'#ffffff',
    font:{family:"-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif",color:'#1f2937'},
    margin:{l:55,r:35,t:10,b:100},xaxis_title:'Accumulated Volume',yaxis_title:'Financial Year',
    yaxis:{categoryorder:'category descending',showgrid:false,zeroline:false,automargin:true},
    xaxis:{showgrid:true,gridcolor:'#F3F4F6',zeroline:false,automargin:true,range:[0,maxTotal*1.25]},
    hovermode:'closest',showlegend:true,
    legend:{title:{text:''},orientation:'h',yanchor:'top',y:-0.22,xanchor:'left',x:0,font:{size:11},itemwidth:65}
  };
  Plotly.react(el,traces,layout,PLOTLY_CFG);
  renderYearlyInsights(rows);
}

function renderYearlyInsights(rows){
  const ul=document.getElementById('yearlyInsights');
  if(!rows.length){ul.innerHTML='<li>No yearly insight available.</li>';return;}
  const totals={};
  rows.forEach(r=>{totals[r.y]=(totals[r.y]||0)+r.c;});
  const sorted=Object.entries(totals).sort((a,b)=>a[0]-b[0]);
  const peak=sorted.reduce((a,b)=>b[1]>a[1]?b:a);
  const items=[`Highest year: ${peak[0]} recorded the largest total with ${Number(peak[1]).toLocaleString()} alerts.`];
  if(sorted.length>1){
    const diff=sorted[sorted.length-1][1]-sorted[0][1];
    items.push(`Long-term direction: yearly workload ${diff>=0?'increased':'decreased'} by ${Math.abs(diff).toLocaleString()} from ${sorted[0][0]} to ${sorted[sorted.length-1][0]}.`);
    let bigJump=null,bigVal=-Infinity;
    for(let i=1;i<sorted.length;i++){const d=sorted[i][1]-sorted[i-1][1];if(d>bigVal){bigVal=d;bigJump=sorted[i];}}
    if(bigJump&&bigVal>0) items.push(`Biggest year-on-year jump: ${bigJump[0]} rose by ${bigVal.toLocaleString()} versus the previous year.`);
  }
  ul.innerHTML=items.map(t=>`<li>${t}</li>`).join('');
}

// ══════════════════════════════════════════════════════
//  MASTER RENDER (dashboard)
// ══════════════════════════════════════════════════════
function render(){
  const rows=filteredRows();
  renderKPIs(rows);
  renderTrend(rows);
  renderStatus(rows);
  renderYearly(rows);
}

function setTrendMode(mode){
  trendMode=mode;
  document.getElementById('btn-total').classList.toggle('active',mode==='total');
  document.getElementById('btn-compare').classList.toggle('active',mode==='compare');
  render();
}

function resetFilters(){
  selStatus=[]; selYears=[]; selMonths=[];
  initDropdowns();
  render();
}

// ══════════════════════════════════════════════════════
//  INIT DROPDOWNS
// ══════════════════════════════════════════════════════
function initDropdowns(){
  const statusOpts=PAYLOAD.names.map(n=>({value:n,label:n}));
  const yearOpts=PAYLOAD.years.map(y=>({value:y,label:String(y)}));
  const monthOpts=PAYLOAD.months;

  // set placeholder data attr
  ['ms-status','ms-year','ms-month'].forEach((id,i)=>{
    document.getElementById(id+'-box').dataset.placeholder=['All statuses','All years','All months'][i];
  });

  buildDropdown('ms-status',statusOpts,selStatus,render);
  buildDropdown('ms-year',yearOpts,selYears,render);
  buildDropdown('ms-month',monthOpts,selMonths,render);
}

// ══════════════════════════════════════════════════════
//  EXPLORER
// ══════════════════════════════════════════════════════
function explorerRows(){
  if(!expStatus.length) return PAYLOAD.rows;
  return PAYLOAD.rows.filter(r=>expStatus.includes(r.n));
}

function renderExplorer(){
  const rows=explorerRows();
  const list=document.getElementById('explorerList');
  list.innerHTML='';

  // group: NAME → year → month → dates
  const tree={};
  rows.forEach(r=>{
    if(!tree[r.n]) tree[r.n]={total:0,years:{}};
    tree[r.n].total+=r.c;
    if(!tree[r.n].years[r.y]) tree[r.n].years[r.y]={total:0,months:{}};
    tree[r.n].years[r.y].total+=r.c;
    if(!tree[r.n].years[r.y].months[r.m]) tree[r.n].years[r.y].months[r.m]={total:0,dates:{}};
    tree[r.n].years[r.y].months[r.m].total+=r.c;
    tree[r.n].years[r.y].months[r.m].dates[r.d]=(tree[r.n].years[r.y].months[r.m].dates[r.d]||0)+r.c;
  });

  if(!Object.keys(tree).length){list.innerHTML='<div class="no-data">No data available.</div>';return;}

  Object.entries(tree).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([name,nData])=>{
    const wrapper=document.createElement('div'); wrapper.className='year-wrapper';
    const nameRow=makeRow('year-row',name,nData.total);
    const yearCont=document.createElement('div'); yearCont.className='sub-container';

    Object.entries(nData.years).sort((a,b)=>b[0]-a[0]).forEach(([yr,yData])=>{
      const yearRow=makeRow('month-row',yr,yData.total);
      const monthCont=document.createElement('div'); monthCont.className='sub-container';

      Object.entries(yData.months).sort((a,b)=>a[0]-b[0]).forEach(([mn,mData])=>{
        const monthRow=makeRow('date-row',MONTH_ABR[mn],mData.total);
        const dateCont=document.createElement('div'); dateCont.className='sub-container';

        Object.entries(mData.dates).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([dt,cnt])=>{
          dateCont.appendChild(makeRow('day-row',dt,cnt,false));
        });

        addToggle(monthRow,dateCont);
        monthCont.appendChild(monthRow); monthCont.appendChild(dateCont);
      });

      addToggle(yearRow,monthCont);
      monthCont.querySelectorAll('.month-row,.date-row,.day-row').forEach(r=>r.addEventListener('click',e=>e.stopPropagation()));
      yearCont.appendChild(yearRow); yearCont.appendChild(monthCont);
    });

    addToggle(nameRow,yearCont);
    wrapper.appendChild(nameRow); wrapper.appendChild(yearCont);
    list.appendChild(wrapper);
  });
}

function makeRow(cls,label,count,expandable=true){
  const row=document.createElement('div'); row.className='table-row '+cls;
  const left=document.createElement('div'); left.className='cell cell-label';
  left.innerHTML=(expandable?'<span class="expand-icon">▶</span> ':'')+label;
  const right=document.createElement('div'); right.className='cell cell-count';
  right.textContent=Number(count).toLocaleString();
  row.appendChild(left); row.appendChild(right);
  return row;
}

function addToggle(row,container){
  row.addEventListener('click',function(e){
    e.stopPropagation();
    const icon=row.querySelector('.expand-icon');
    const open=container.style.display==='block';
    container.style.display=open?'none':'block';
    if(icon) icon.textContent=open?'▶':'▼';
  });
}

function resetExplorer(){
  expStatus=[];
  buildDropdown('ms-exp-status',PAYLOAD.names.map(n=>({value:n,label:n})),expStatus,renderExplorer);
  renderExplorer();
}

// ══════════════════════════════════════════════════════
//  BOOT
// ══════════════════════════════════════════════════════
(function init(){
  initDropdowns();
  document.getElementById('ms-exp-status-box').dataset.placeholder='All statuses';
  buildDropdown('ms-exp-status',PAYLOAD.names.map(n=>({value:n,label:n})),expStatus,renderExplorer);
  render();
})();
</script>
</body>
</html>
"""

# ── Write output ───────────────────────────────────────────────────────────────
def main():
    print("Fetching Plotly.js (needed once for offline embedding)...")
    plotly_js = fetch_plotly_js()

    print("Loading data from Parquet files...")
    df = load_data()
    print(f"  → {df.height:,} aggregated rows loaded.")

    print("Building data payload...")
    payload = build_payload(df)
    names_count, years_count, rows_count = len(payload["names"]), len(payload["years"]), len(payload["rows"])
    print(f"  → {names_count} statuses | {years_count} years | {rows_count:,} rows")

    payload_json = json.dumps(payload, separators=(',', ':'))

    print("Generating HTML...")
    html = HTML_TEMPLATE.replace("__PLOTLY_JS__", plotly_js)
    html = html.replace("__PAYLOAD__", payload_json)

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    size_str = f"{size_kb/1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"
    print(f"\n✅  Done! Output: {OUTPUT_PATH}")
    print(f"   File size: {size_str}")
    print("\nSend 'dashboard.html' to the higher-ups.")
    print("They can open it with NO internet, NO Python, NO server — just double-click.")


if __name__ == "__main__":
    main()
