"""Data & dashboard exporters."""
from __future__ import annotations
import io
import json
import pandas as pd
from typing import Any
import plotly


def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Data")
    return buf.getvalue()

def to_json(df: pd.DataFrame) -> bytes:
    return df.to_json(orient="records", date_format="iso").encode("utf-8")


def to_html_dashboard(df, profile, charts, kpis, insights) -> str:
    """Generates a premium, standalone HTML dashboard."""
    
    # Serialize charts to JSON for Plotly.js
    chart_jsons = [json.dumps(c["fig"], cls=plotly.utils.PlotlyJSONEncoder) for c in charts]
    
    # KPI Cards HTML
    kpi_colors = ["#7C3AED", "#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"]
    kpi_html = ""
    for i, (k, v) in enumerate(list(kpis.items())[:6]):
        val = v if not isinstance(v, dict) else ", ".join(f"{k2}:{v2}" for k2,v2 in list(v.items())[:2])
        color = kpi_colors[i % len(kpi_colors)]
        kpi_html += f"""
        <div class="kpi-card" style="border-left: 4px solid {color};">
            <div class="kpi-title">{k}</div>
            <div class="kpi-value">{val}</div>
        </div>
        """
    
    # Insights HTML
    sev_colors = {"info": "#06B6D4", "warning": "#F59E0B", "danger": "#EF4444"}
    ins_html = ""
    for ins in insights:
        color = sev_colors.get(ins['severity'], '#06B6D4')
        ins_html += f"""
        <div class="insight-card" style="border-left: 4px solid {color};">
            <div class="ins-title">{ins['title']} <span class="ins-badge">{ins['category']}</span></div>
            <div class="ins-body">{ins['body']}</div>
        </div>
        """
        
    # Chart Grid HTML
    chart_html = ""
    for i, c_json in enumerate(chart_jsons):
        chart_html += f'<div class="chart-card"><div id="plotly-chart-{i}"></div></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus BI Dashboard Export</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0B1020; --bg-2: #131A33; --card: rgba(255,255,255,0.03);
            --border: rgba(255,255,255,0.08); --text: #E5E7EB; --muted: #9CA3AF;
            --accent: #7C3AED; --accent-2: #4F46E5;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text);
            background-image: 
                radial-gradient(1200px 600px at 80% -10%, rgba(124,58,237,0.15), transparent 60%),
                radial-gradient(800px 500px at -10% 110%, rgba(79,70,229,0.12), transparent 60%);
            background-attachment: fixed; min-height: 100vh; padding: 40px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 42px; font-weight: 800; background: linear-gradient(135deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header p {{ color: var(--muted); margin-top: 10px; font-size: 16px; }}
        
        .grid-3 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .grid-2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        
        .glass {{
            background: var(--card); backdrop-filter: blur(18px); border: 1px solid var(--border);
            border-radius: 16px; padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        }}
        .kpi-card {{ padding: 20px; }}
        .kpi-title {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
        .kpi-value {{ font-size: 28px; font-weight: 700; margin-top: 8px; color: var(--text); }}
        
        .chart-card {{ min-height: 400px; padding: 16px; }}
        
        .insight-card {{ padding: 18px; margin-bottom: 12px; background: var(--card); border-radius: 12px; border: 1px solid var(--border); }}
        .ins-title {{ font-weight: 700; font-size: 15px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }}
        .ins-badge {{ font-size: 10px; background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 99px; color: var(--muted); font-weight: 500; }}
        .ins-body {{ font-size: 13px; color: var(--muted); line-height: 1.6; }}
        
        .section-title {{ font-size: 20px; font-weight: 700; margin: 40px 0 20px 0; display: flex; align-items: center; gap: 10px; }}
        .section-title::before {{ content: ''; width: 4px; height: 20px; background: var(--accent); border-radius: 2px; }}
        
        footer {{ text-align: center; margin-top: 60px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--border); padding-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Nexus BI Dashboard</h1>
            <p>AI-Generated Analytics Report • {profile.rows:,} Rows • {profile.cols} Columns</p>
        </div>
        
        <div class="section-title">Key Performance Indicators</div>
        <div class="grid-3">
            {kpi_html}
        </div>
        
        <div class="section-title">Visualizations</div>
        <div class="grid-2">
            {chart_html}
        </div>
        
        <div class="section-title">AI Insights</div>
        <div class="grid-2">
            {ins_html}
        </div>
        
        <footer>
            Generated by Nexus BI Enterprise AI Dashboard Builder
        </footer>
    </div>

    <script>
        // Render Plotly Charts
        const charts = {json.dumps(chart_jsons)};
        charts.forEach((chartData, i) => {{
            const divId = `plotly-chart-${{i}}`;
            Plotly.newPlot(divId, chartData.data, chartData.layout, {{responsive: true, displayModeBar: false}});
        }});
    </script>
</body>
</html>"""