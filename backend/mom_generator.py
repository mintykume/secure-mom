"""Turns structured extraction output into a readable MoM document."""
from datetime import datetime


def _table_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>")


def generate_mom_markdown(
    meeting_type: str,
    meeting_id: str,
    extraction: dict,
    detected_language: str | None,
    transcript_excerpt: str,
) -> str:
    lines = [
        f"# Minutes of Meeting — {meeting_type.title()}",
        f"_Meeting ID: {meeting_id} · Generated: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        f"Detected language: {detected_language or 'unknown'}_",
        "",
        "## Summary",
        extraction.get("meeting_summary") or "_(no summary extracted)_",
        "",
        "## Action items",
        "",
        "| Decision | Owner | Deadline |",
        "|---|---|---|",
    ]

    items = extraction.get("action_items") or []
    if not items:
        lines.append("| _(no action items extracted)_ | | |")
    for item in items:
        decision = _table_cell(item.get("decision") or "")
        owner = _table_cell(item.get("owner") or "—")
        deadline = _table_cell(item.get("deadline") or "—")
        lines.append(f"| {decision} | {owner} | {deadline} |")

    lines += [
        "",
        "## Transcript excerpt",
        "",
        (transcript_excerpt or "")[:2000],
    ]
    return "\n".join(lines)
