#!/usr/bin/env python3
"""
AWS IAM Security Audit Visualizer
Generates an interactive, modern web dashboard and SVG charts from audit-report.json.
Zero external Python dependencies required.
"""

import argparse
import json
import os
import sys
import webbrowser
from collections import Counter
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


def load_report(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_metrics(data):
    total = len(data)
    status_counts = Counter(item.get("status", "UNKNOWN") for item in data)
    severity_counts = Counter(item.get("severity", "UNKNOWN") for item in data)
    
    # Regional breakdown (especially control 2.18)
    regions = Counter(item.get("region", "global") for item in data)
    
    pass_count = status_counts.get("PASS", 0)
    fail_count = status_counts.get("FAIL", 0)
    error_count = status_counts.get("ERROR", 0)
    manual_count = status_counts.get("MANUAL", 0)
    na_count = status_counts.get("NOT_APPLICABLE", 0)
    
    # Compliance score based on evaluated actionable controls (Pass / (Pass + Fail))
    evaluable = pass_count + fail_count
    compliance_score = round((pass_count / evaluable * 100), 1) if evaluable > 0 else 0.0

    return {
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "error": error_count,
        "manual": manual_count,
        "na": na_count,
        "compliance_score": compliance_score,
        "status_counts": dict(status_counts),
        "severity_counts": dict(severity_counts),
        "region_counts": dict(regions)
    }


def generate_svg_chart(metrics: dict, output_path: Path):
    """Generate standalone SVG charts without any 3rd party dependencies."""
    status = metrics["status_counts"]
    pass_cnt = status.get("PASS", 0)
    fail_cnt = status.get("FAIL", 0)
    err_cnt = status.get("ERROR", 0)
    man_cnt = status.get("MANUAL", 0)
    na_cnt = status.get("NOT_APPLICABLE", 0)
    total = metrics["total"] or 1

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 360" width="100%" height="360" style="background: #0f172a; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <style>
    .title {{ fill: #f8fafc; font-size: 18px; font-weight: bold; }}
    .subtitle {{ fill: #94a3b8; font-size: 13px; }}
    .label {{ fill: #cbd5e1; font-size: 13px; font-weight: 500; }}
    .val {{ fill: #ffffff; font-size: 13px; font-weight: bold; }}
    .bar-bg {{ fill: #1e293b; rx: 6px; }}
    .stat-box {{ fill: #1e293b; rx: 8px; stroke: #334155; stroke-width: 1px; }}
    .stat-num {{ font-size: 24px; font-weight: 800; }}
    .stat-lbl {{ fill: #94a3b8; font-size: 12px; font-weight: 500; text-transform: uppercase; }}
  </style>

  <!-- Header -->
  <text x="30" y="42" class="title">AWS IAM Security Audit Overview</text>
  <text x="30" y="65" class="subtitle">CIS AWS Foundations Benchmark Controls • Total Findings: {total}</text>

  <!-- Metric Badges -->
  <g transform="translate(30, 85)">
    <!-- Score -->
    <rect x="0" y="0" width="130" height="65" class="stat-box" />
    <text x="15" y="32" class="stat-num" fill="#38bdf8">{metrics['compliance_score']}%</text>
    <text x="15" y="52" class="stat-lbl">Actionable Pass</text>

    <!-- Failed -->
    <rect x="150" y="0" width="130" height="65" class="stat-box" />
    <text x="165" y="32" class="stat-num" fill="#f87171">{fail_cnt}</text>
    <text x="165" y="52" class="stat-lbl">Failed Controls</text>

    <!-- Errors -->
    <rect x="300" y="0" width="130" height="65" class="stat-box" />
    <text x="315" y="32" class="stat-num" fill="#fb923c">{err_cnt}</text>
    <text x="315" y="52" class="stat-lbl">Permission Errors</text>

    <!-- Passed -->
    <rect x="450" y="0" width="130" height="65" class="stat-box" />
    <text x="465" y="32" class="stat-num" fill="#4ade80">{pass_cnt}</text>
    <text x="465" y="52" class="stat-lbl">Passed</text>

    <!-- N/A & Manual -->
    <rect x="600" y="0" width="140" height="65" class="stat-box" />
    <text x="615" y="32" class="stat-num" fill="#a78bfa">{man_cnt + na_cnt}</text>
    <text x="615" y="52" class="stat-lbl">N/A & Manual</text>
  </g>

  <!-- Progress Bar Breakdown -->
  <g transform="translate(30, 185)">
    <text x="0" y="0" class="label" font-size="14">Findings Distribution</text>
    
    <!-- Full bar background -->
    <rect x="0" y="15" width="740" height="24" rx="12" fill="#1e293b" />
    <g>
      <!-- PASS -->
      <rect x="0" y="15" width="{round(740 * pass_cnt / total)}" height="24" rx="6" fill="#10b981" />
      <!-- FAIL -->
      <rect x="{round(740 * pass_cnt / total)}" y="15" width="{round(740 * fail_cnt / total)}" height="24" rx="6" fill="#ef4444" />
      <!-- ERROR -->
      <rect x="{round(740 * (pass_cnt + fail_cnt) / total)}" y="15" width="{round(740 * err_cnt / total)}" height="24" rx="6" fill="#f59e0b" />
      <!-- MANUAL -->
      <rect x="{round(740 * (pass_cnt + fail_cnt + err_cnt) / total)}" y="15" width="{round(740 * man_cnt / total)}" height="24" rx="6" fill="#8b5cf6" />
      <!-- NA -->
      <rect x="{round(740 * (pass_cnt + fail_cnt + err_cnt + man_cnt) / total)}" y="15" width="{round(740 * na_cnt / total)}" height="24" rx="6" fill="#64748b" />
    </g>
  </g>

  <!-- Legend -->
  <g transform="translate(30, 260)">
    <!-- Pass -->
    <circle cx="10" cy="10" r="7" fill="#10b981" />
    <text x="25" y="15" class="label">PASS ({pass_cnt})</text>

    <!-- Fail -->
    <circle cx="140" cy="10" r="7" fill="#ef4444" />
    <text x="155" y="15" class="label">FAIL ({fail_cnt})</text>

    <!-- Error -->
    <circle cx="270" cy="10" r="7" fill="#f59e0b" />
    <text x="285" y="15" class="label">ERROR ({err_cnt})</text>

    <!-- Manual -->
    <circle cx="410" cy="10" r="7" fill="#8b5cf6" />
    <text x="425" y="15" class="label">MANUAL ({man_cnt})</text>

    <!-- N/A -->
    <circle cx="560" cy="10" r="7" fill="#64748b" />
    <text x="575" y="15" class="label">N/A ({na_cnt})</text>
  </g>

  <!-- Footer note -->
  <text x="30" y="325" fill="#64748b" font-size="11">Generated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} • Source: audit-report.json</text>
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)


def generate_html_dashboard(data: list, metrics: dict, output_path: Path):
    """Generate a responsive HTML dashboard with interactive charts and filters."""
    json_data_str = json.dumps(data).replace("</script>", "<\\/script>")
    metrics_str = json.dumps(metrics)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AWS IAM Security Audit Dashboard</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Chart.js CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            slate: {{
              850: '#151f33',
              900: '#0f172a',
              950: '#090d16'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    pre code {{
      font-family: 'JetBrains Mono', 'Fira Code', Menlo, Consolas, monospace;
    }}
    .custom-scroll::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    .custom-scroll::-webkit-scrollbar-thumb {{
      background: #475569;
      border-radius: 4px;
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased selection:bg-indigo-500 selection:text-white">

  <!-- Navigation Bar -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="p-2 bg-gradient-to-tr from-indigo-600 to-amber-500 rounded-lg text-white shadow-lg shadow-indigo-500/20">
          <i class="fa-solid fa-shield-halved text-xl"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-lg font-bold tracking-tight text-white">AWS IAM Security Audit</h1>
            <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">CIS Benchmark</span>
          </div>
          <p class="text-xs text-slate-400">Read-only IAM & Access Analyzer Evaluation</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <button onclick="window.print()" class="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition flex items-center gap-1.5 shadow-sm">
          <i class="fa-solid fa-print"></i> <span>Print / PDF</span>
        </button>
        <button onclick="exportJSON()" class="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition flex items-center gap-1.5 shadow-md shadow-indigo-600/30">
          <i class="fa-solid fa-download"></i> <span>Export JSON</span>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

    <!-- KPI Metric Cards -->
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <!-- Total -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div class="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Total Checks</span>
          <i class="fa-solid fa-list-check text-slate-500"></i>
        </div>
        <div class="text-2xl font-extrabold text-white" id="kpi-total">{metrics['total']}</div>
        <div class="text-xs text-slate-500 mt-1">10 Global + 17 Regions</div>
      </div>

      <!-- Compliance Score -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div class="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Pass Rate</span>
          <i class="fa-solid fa-chart-pie text-sky-400"></i>
        </div>
        <div class="text-2xl font-extrabold text-sky-400">{metrics['compliance_score']}%</div>
        <div class="text-xs text-slate-500 mt-1">of evaluated controls</div>
      </div>

      <!-- Failed -->
      <div class="bg-slate-900 border border-rose-900/30 rounded-xl p-4 shadow-sm hover:border-rose-700/50 transition">
        <div class="text-rose-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Failed</span>
          <i class="fa-solid fa-circle-xmark text-rose-500"></i>
        </div>
        <div class="text-2xl font-extrabold text-rose-400">{metrics['fail']}</div>
        <div class="text-xs text-rose-500/80 mt-1">Immediate action needed</div>
      </div>

      <!-- Errors -->
      <div class="bg-slate-900 border border-amber-900/30 rounded-xl p-4 shadow-sm hover:border-amber-700/50 transition">
        <div class="text-amber-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Errors</span>
          <i class="fa-solid fa-triangle-exclamation text-amber-500"></i>
        </div>
        <div class="text-2xl font-extrabold text-amber-400">{metrics['error']}</div>
        <div class="text-xs text-amber-500/80 mt-1">Permission denied</div>
      </div>

      <!-- Passed -->
      <div class="bg-slate-900 border border-emerald-900/30 rounded-xl p-4 shadow-sm hover:border-emerald-700/50 transition">
        <div class="text-emerald-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Passed</span>
          <i class="fa-solid fa-circle-check text-emerald-500"></i>
        </div>
        <div class="text-2xl font-extrabold text-emerald-400">{metrics['pass']}</div>
        <div class="text-xs text-emerald-500/80 mt-1">Compliant controls</div>
      </div>

      <!-- Manual & N/A -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div class="text-purple-400 text-xs font-medium uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Manual / N/A</span>
          <i class="fa-solid fa-eye text-purple-400"></i>
        </div>
        <div class="text-2xl font-extrabold text-purple-300">{metrics['manual'] + metrics['na']}</div>
        <div class="text-xs text-slate-500 mt-1">{metrics['manual']} Manual, {metrics['na']} N/A</div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Status Donut Chart -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-sm font-semibold text-slate-200">Status Distribution</h2>
          <span class="text-xs text-slate-500">Breakdown</span>
        </div>
        <div class="relative h-60 flex items-center justify-center">
          <canvas id="statusChart"></canvas>
        </div>
      </div>

      <!-- Regional Breakdown Bar Chart -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-sm font-semibold text-slate-200">Multi-Region Access Analyzer (Control 2.18)</h2>
            <p class="text-xs text-slate-400">Status across 17 audited AWS regions</p>
          </div>
          <span class="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">17 Regions</span>
        </div>
        <div class="relative h-60">
          <canvas id="regionChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Findings Table Section -->
    <div class="bg-slate-900 border border-slate-800 rounded-xl shadow-sm overflow-hidden">
      <!-- Filter Bar & Search -->
      <div class="p-5 border-b border-slate-800 space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-white">Detailed Audit Findings</h2>
            <p class="text-xs text-slate-400">Click any row to inspect technical evidence and remediation</p>
          </div>
          
          <!-- Search input -->
          <div class="relative w-full md:w-80">
            <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-500 text-xs"></i>
            <input 
              type="text" 
              id="searchInput" 
              placeholder="Search by ID, title, region, or message..." 
              oninput="applyFilter()"
              class="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <!-- Filter Chips -->
        <div class="flex flex-wrap items-center gap-2 pt-1 text-xs">
          <span class="text-slate-400 font-medium mr-1">Filter by Status:</span>
          <button onclick="setStatusFilter('ALL')" id="chip-ALL" class="filter-chip px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium transition shadow-sm">All ({metrics['total']})</button>
          <button onclick="setStatusFilter('FAIL')" id="chip-FAIL" class="filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition">Fail ({metrics['fail']})</button>
          <button onclick="setStatusFilter('ERROR')" id="chip-ERROR" class="filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition">Error ({metrics['error']})</button>
          <button onclick="setStatusFilter('PASS')" id="chip-PASS" class="filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition">Pass ({metrics['pass']})</button>
          <button onclick="setStatusFilter('MANUAL')" id="chip-MANUAL" class="filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition">Manual ({metrics['manual']})</button>
          <button onclick="setStatusFilter('NOT_APPLICABLE')" id="chip-NOT_APPLICABLE" class="filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition">N/A ({metrics['na']})</button>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto custom-scroll">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[11px]">
              <th class="py-3 px-4 w-20">Control</th>
              <th class="py-3 px-4 w-28">Status</th>
              <th class="py-3 px-4 w-20">Severity</th>
              <th class="py-3 px-4 w-28">Region</th>
              <th class="py-3 px-4">Title & Message</th>
              <th class="py-3 px-4 w-28 text-right">Details</th>
            </tr>
          </thead>
          <tbody id="findingsTableBody" class="divide-y divide-slate-800/60 font-normal">
            <!-- Rendered by JS -->
          </tbody>
        </table>
      </div>

      <!-- Empty state -->
      <div id="emptyState" class="hidden py-12 text-center text-slate-500">
        <i class="fa-regular fa-folder-open text-3xl mb-2 text-slate-600"></i>
        <p class="text-sm">No findings matched your search or filter.</p>
      </div>

      <div class="p-4 border-t border-slate-800/80 bg-slate-950/40 text-xs text-slate-500 flex justify-between items-center">
        <span id="showingCount">Showing {metrics['total']} findings</span>
        <span>Source: <code>audit-report.json</code></span>
      </div>
    </div>

  </main>

  <footer class="border-t border-slate-800 py-6 mt-12 text-center text-xs text-slate-500">
    <p>AWS IAM Security Audit Visualizer • Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
  </footer>

  <script>
    const reportData = {json_data_str};
    const reportMetrics = {metrics_str};
    let currentStatusFilter = 'ALL';

    const statusBadgeStyles = {{
      'PASS': 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
      'FAIL': 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
      'ERROR': 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
      'MANUAL': 'bg-purple-500/10 text-purple-400 border border-purple-500/20',
      'NOT_APPLICABLE': 'bg-slate-700/30 text-slate-400 border border-slate-700/50'
    }};

    const severityBadgeStyles = {{
      'HIGH': 'text-rose-400 font-semibold',
      'MEDIUM': 'text-amber-400 font-medium',
      'LOW': 'text-slate-400'
    }};

    function renderTable() {{
      const tbody = document.getElementById('findingsTableBody');
      const search = document.getElementById('searchInput').value.toLowerCase().trim();
      const emptyState = document.getElementById('emptyState');
      tbody.innerHTML = '';

      let matchedCount = 0;

      reportData.forEach((item, index) => {{
        const matchesStatus = (currentStatusFilter === 'ALL' || item.status === currentStatusFilter);
        const matchesSearch = !search || 
          (item.control_id && item.control_id.toLowerCase().includes(search)) ||
          (item.title && item.title.toLowerCase().includes(search)) ||
          (item.region && item.region.toLowerCase().includes(search)) ||
          (item.message && item.message.toLowerCase().includes(search));

        if (!matchesStatus || !matchesSearch) return;

        matchedCount++;
        const badgeClass = statusBadgeStyles[item.status] || 'bg-slate-800 text-slate-300';
        const sevClass = severityBadgeStyles[item.severity] || 'text-slate-400';
        const rowId = `finding-${{index}}`;
        const detailId = `detail-${{index}}`;

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-850/80 cursor-pointer transition';
        tr.onclick = () => toggleDetail(detailId, `chevron-${{index}}`);
        tr.innerHTML = `
          <td class="py-3 px-4 font-mono font-bold text-indigo-400">${{item.control_id}}</td>
          <td class="py-3 px-4">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${{badgeClass}}">
              ${{item.status}}
            </span>
          </td>
          <td class="py-3 px-4 ${{sevClass}}">${{item.severity}}</td>
          <td class="py-3 px-4 font-mono text-slate-300">${{item.region}}</td>
          <td class="py-3 px-4">
            <div class="font-medium text-slate-200">${{item.title}}</div>
            <div class="text-[11px] text-slate-400 truncate max-w-xl">${{item.message || 'No additional message'}}</div>
          </td>
          <td class="py-3 px-4 text-right">
            <i id="chevron-${{index}}" class="fa-solid fa-chevron-down text-slate-500 transition-transform duration-200"></i>
          </td>
        `;

        const detailTr = document.createElement('tr');
        detailTr.id = detailId;
        detailTr.className = 'hidden bg-slate-950/70 border-b border-slate-800';
        detailTr.innerHTML = `
          <td colspan="6" class="p-5 space-y-4">
            ${{item.remediation ? `
              <div class="bg-rose-950/30 border border-rose-900/50 rounded-lg p-3.5 text-xs">
                <span class="font-semibold text-rose-400 flex items-center gap-1.5 mb-1">
                  <i class="fa-solid fa-wrench"></i> Suggested Remediation:
                </span>
                <p class="text-slate-300">${{item.remediation}}</p>
              </div>
            ` : ''}}

            <div class="space-y-1.5">
              <span class="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <i class="fa-solid fa-code text-indigo-400"></i> Technical Evidence & Context:
              </span>
              <pre class="bg-slate-900 border border-slate-800 text-slate-300 p-3 rounded-lg overflow-x-auto text-[11px] custom-scroll"><code>${{JSON.stringify(item.evidence || {{}}, null, 2)}}</code></pre>
            </div>

            <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1">
              <span>Resource ID: <code class="text-slate-400">${{item.resource_id}}</code></span>
              <span>Checked At: ${{item.checked_at}}</span>
            </div>
          </td>
        `;

        tbody.appendChild(tr);
        tbody.appendChild(detailTr);
      }});

      document.getElementById('showingCount').textContent = `Showing ${{matchedCount}} of ${{reportData.length}} findings`;
      if (matchedCount === 0) {{
        emptyState.classList.remove('hidden');
      }} else {{
        emptyState.classList.add('hidden');
      }}
    }}

    function toggleDetail(detailId, chevronId) {{
      const detailEl = document.getElementById(detailId);
      const chevronEl = document.getElementById(chevronId);
      if (detailEl.classList.contains('hidden')) {{
        detailEl.classList.remove('hidden');
        chevronEl.style.transform = 'rotate(180deg)';
      }} else {{
        detailEl.classList.add('hidden');
        chevronEl.style.transform = 'rotate(0deg)';
      }}
    }}

    function setStatusFilter(status) {{
      currentStatusFilter = status;
      document.querySelectorAll('.filter-chip').forEach(chip => {{
        chip.className = 'filter-chip px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition';
      }});
      const activeChip = document.getElementById(`chip-${{status}}`);
      if (activeChip) {{
        activeChip.className = 'filter-chip px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium transition shadow-sm';
      }}
      renderTable();
    }}

    function applyFilter() {{
      renderTable();
    }}

    function exportJSON() {{
      const blob = new Blob([JSON.stringify(reportData, null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'audit-report-export.json';
      a.click();
      URL.revokeObjectURL(url);
    }}

    // Initialize Chart.js Charts
    function initCharts() {{
      // Status Donut
      const statusCounts = reportMetrics.status_counts;
      const statusLabels = Object.keys(statusCounts);
      const statusData = Object.values(statusCounts);
      const statusColors = statusLabels.map(s => {{
        if (s === 'PASS') return '#10b981';
        if (s === 'FAIL') return '#ef4444';
        if (s === 'ERROR') return '#f59e0b';
        if (s === 'MANUAL') return '#8b5cf6';
        return '#64748b';
      }});

      new Chart(document.getElementById('statusChart'), {{
        type: 'doughnut',
        data: {{
          labels: statusLabels,
          datasets: [{{
            data: statusData,
            backgroundColor: statusColors,
            borderColor: '#0f172a',
            borderWidth: 3
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{
              position: 'bottom',
              labels: {{ color: '#94a3b8', font: {{ size: 11 }} }}
            }}
          }},
          cutout: '65%'
        }}
      }});

      // Regional Access Analyzer Breakdown
      const regionFindings = reportData.filter(d => d.control_id === '2.18');
      const regions = [...new Set(regionFindings.map(d => d.region))];
      
      const regionPass = [];
      const regionFail = [];
      const regionError = [];

      regions.forEach(r => {{
        const items = regionFindings.filter(d => d.region === r);
        regionPass.push(items.filter(d => d.status === 'PASS').length);
        regionFail.push(items.filter(d => d.status === 'FAIL').length);
        regionError.push(items.filter(d => d.status === 'ERROR').length);
      }});

      new Chart(document.getElementById('regionChart'), {{
        type: 'bar',
        data: {{
          labels: regions,
          datasets: [
            {{ label: 'Fail (Disabled)', data: regionFail, backgroundColor: '#ef4444' }},
            {{ label: 'Error (Denied/Unreachable)', data: regionError, backgroundColor: '#f59e0b' }},
            {{ label: 'Pass (Active)', data: regionPass, backgroundColor: '#10b981' }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{
              stacked: true,
              ticks: {{ color: '#64748b', font: {{ size: 10 }}, maxRotation: 45 }},
              grid: {{ display: false }}
            }},
            y: {{
              stacked: true,
              ticks: {{ color: '#64748b', precision: 0 }},
              grid: {{ color: '#1e293b' }}
            }}
          }},
          plugins: {{
            legend: {{
              position: 'top',
              labels: {{ color: '#94a3b8', font: {{ size: 11 }} }}
            }}
          }}
        }}
      }});
    }}

    document.addEventListener('DOMContentLoaded', () => {{
      renderTable();
      initCharts();
    }});
  </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def start_server(port: int, directory: Path):
    os.chdir(directory)
    handler = SimpleHTTPRequestHandler
    httpd = HTTPServer(("127.0.0.1", port), handler)
    print(f"🚀 Serving audit report on: http://127.0.0.1:{port}/audit-report.html")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")


def main():
    parser = argparse.ArgumentParser(description="Visualize AWS IAM Audit Report")
    parser.add_argument(
        "--input", "-i",
        default="audit-report.json",
        help="Path to input audit-report.json (default: audit-report.json)"
    )
    parser.add_argument(
        "--output-html",
        default="audit-report.html",
        help="Output HTML dashboard path (default: audit-report.html)"
    )
    parser.add_argument(
        "--output-svg",
        default="audit-chart.svg",
        help="Output standalone SVG chart path (default: audit-chart.svg)"
    )
    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Open HTML report directly in default web browser"
    )
    parser.add_argument(
        "--serve", "-s",
        action="store_true",
        help="Start a local web server to host the report"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for local web server (default: 8000)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = Path.cwd() / input_path

    out_html = Path(args.output_html)
    if not out_html.is_absolute():
        out_html = Path.cwd() / out_html

    out_svg = Path(args.output_svg)
    if not out_svg.is_absolute():
        out_svg = Path.cwd() / out_svg

    print(f"[*] Reading audit report from: {input_path}")
    data = load_report(input_path)
    metrics = calculate_metrics(data)

    print(f"[*] Total findings: {metrics['total']}")
    print(f"    - PASS: {metrics['pass']}")
    print(f"    - FAIL: {metrics['fail']}")
    print(f"    - ERROR: {metrics['error']}")
    print(f"    - MANUAL: {metrics['manual']}")
    print(f"    - N/A: {metrics['na']}")
    print(f"    - Compliance Score: {metrics['compliance_score']}%")

    # Generate HTML
    generate_html_dashboard(data, metrics, out_html)
    print(f"[+] Generated Interactive HTML Dashboard: {out_html}")

    # Generate standalone SVG
    generate_svg_chart(metrics, out_svg)
    print(f"[+] Generated Standalone SVG Chart: {out_svg}")

    if args.open:
        webbrowser.open(out_html.as_uri())

    if args.serve:
        start_server(args.port, out_html.parent)


if __name__ == "__main__":
    main()
