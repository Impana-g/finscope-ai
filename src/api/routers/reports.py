# reports.py router
# Handles everything about reports
# GET /reports/{id}          → get one report
# GET /reports/{id}/export   → download as markdown or html

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse

router = APIRouter()


# ── Import Skandan's DB function ──────────────────────
# If his code isn't ready yet, use the stub below
try:
    from src.db.reports import get_report_by_id  # type: ignore
except ImportError:
    print(" Skandan's db/reports.py not ready yet — using stub")
    def get_report_by_id(report_id: str):
        return None


# ── Endpoints ─────────────────────────────────────────

@router.get("/{report_id}")
def get_one_report(report_id: str):
    """
    Get a specific report by its ID.

    Example: GET /reports/abc-123
    """
    report = get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"No report found with ID: {report_id}",
                "hint": "Make sure research is completed first"
            }
        )

    return report


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    format: str = "markdown"
):
    """
    Download report as markdown or html file.

    Example: GET /reports/abc-123/export?format=markdown
    Example: GET /reports/abc-123/export?format=html
    """
    # Validate format
    if format not in ["markdown", "html"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_format",
                "message": "Format must be 'markdown' or 'html'",
                "valid_formats": ["markdown", "html"]
            }
        )

    report = get_report_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": f"No report found with ID: {report_id}"
            }
        )

    if format == "markdown":
        # Get or build markdown content
        content = report.get("markdown_export") or build_markdown(report)
        filename = f"finscope_report_{report_id[:8]}.md"

        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    elif format == "html":
        content = build_html(report)
        filename = f"finscope_report_{report_id[:8]}.html"

        return HTMLResponse(
            content=content,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )


# ── Helper Functions ──────────────────────────────────

def build_markdown(report: dict) -> str:
    """Build markdown text from report dictionary"""

    md = "# FinScope AI — Research Report\n\n"
    md += "---\n\n"

    # Executive Summary
    md += "## Executive Summary\n\n"
    md += f"{report.get('executive_summary', 'No summary available.')}\n\n"

    # Sections
    for section in report.get("sections", []):
        title = section.get("title", "Section")
        content = section.get("content", "")
        md += f"## {title}\n\n{content}\n\n"

        # Data points
        data_points = section.get("data_points", [])
        if data_points:
            md += "| Metric | Value | Period |\n"
            md += "|--------|-------|--------|\n"
            for dp in data_points:
                md += f"| {dp.get('label','')} | {dp.get('value','')} | {dp.get('period','')} |\n"
            md += "\n"

    # Key Metrics
    key_metrics = report.get("key_metrics", {})
    if key_metrics:
        md += "## Key Metrics\n\n"
        for key, val in key_metrics.items():
            md += f"- **{key}**: {val}\n"
        md += "\n"

    # Investment Outlook
    if report.get("investment_outlook"):
        md += "## Investment Outlook\n\n"
        md += f"{report['investment_outlook']}\n\n"

    # Risk Factors
    risks = report.get("risk_factors", [])
    if risks:
        md += "## Risk Factors\n\n"
        for risk in risks:
            md += f"- {risk}\n"
        md += "\n"

    # Sources
    citations = report.get("citations", [])
    if citations:
        md += "## Sources\n\n"
        for cite in citations:
            url = cite.get("url", "")
            if url:
                md += f"- {url}\n"

    return md


def build_html(report: dict) -> str:
    """Build clean HTML from report dictionary"""

    sections_html = ""
    for section in report.get("sections", []):
        title = section.get("title", "")
        content = section.get("content", "")
        sections_html += f"""
        <div class="section">
            <h2>{title}</h2>
            <p>{content}</p>
        </div>
        """

    risks_html = ""
    for risk in report.get("risk_factors", []):
        risks_html += f"<li>{risk}</li>"

    sources_html = ""
    for cite in report.get("citations", []):
        url = cite.get("url", "")
        if url:
            sources_html += f'<li><a href="{url}">{url}</a></li>'

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>FinScope AI Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                color: #333;
                line-height: 1.6;
            }}
            h1 {{ color: #1a1a2e; border-bottom: 3px solid #1a1a2e; }}
            h2 {{ color: #16213e; margin-top: 30px; }}
            .summary {{
                background: #f0f4ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .section {{ margin: 20px 0; }}
            .risks li {{ color: #c0392b; }}
            a {{ color: #2980b9; }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ccc;
                font-size: 12px;
                color: #888;
            }}
        </style>
    </head>
    <body>
        <h1>FinScope AI — Research Report</h1>

        <div class="summary">
            <h2>Executive Summary</h2>
            <p>{report.get('executive_summary', '')}</p>
        </div>

        {sections_html}

        <div class="section">
            <h2>Investment Outlook</h2>
            <p>{report.get('investment_outlook', 'N/A')}</p>
        </div>

        <div class="section">
            <h2>Risk Factors</h2>
            <ul class="risks">{risks_html}</ul>
        </div>

        <div class="section">
            <h2>Sources</h2>
            <ul>{sources_html}</ul>
        </div>

        <div class="footer">
            Generated by FinScope AI v2.0 |
            Confidence Score: {report.get('confidence_avg', 0)}
        </div>
    </body>
    </html>
    """

    return html
