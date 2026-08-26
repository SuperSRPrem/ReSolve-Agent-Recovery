import json
import html
import streamlit as st


def status_class(status: str) -> str:
    status = (status or "").upper()
    if status in {"RECOVERED", "SUCCESS", "HEALTHY"}:
        return "status-success"
    if status in {"AWAITING_APPROVAL", "PENDING_APPROVAL", "PAUSED", "IN_PROGRESS", "RUNNING", "READY"}:
        return "status-pending"
    if status in {"FAILED", "ESCALATED", "LOAD_FAILED", "ERROR", "TICKET_CREATE_FAILED"}:
        return "status-danger"
    return "status-neutral"


def status_badge(status: str):
    safe = html.escape(status or "UNKNOWN")
    st.markdown(f'<span class="status-pill {status_class(status)}">{safe}</span>', unsafe_allow_html=True)


def metric_card(label, value, detail=None):
    detail_html = f'<div class="metric-detail">{html.escape(str(detail))}</div>' if detail else ""
    st.markdown(f'''<div class="metric-card"><div class="metric-label">{html.escape(str(label))}</div><div class="metric-value">{html.escape(str(value))}</div>{detail_html}</div>''', unsafe_allow_html=True)


def glass_heading(label, caption=None):
    caption_html = f'<div class="section-caption">{html.escape(caption)}</div>' if caption else ""
    st.markdown(f'<div class="section-heading"><div class="section-label">{html.escape(label)}</div>{caption_html}</div>', unsafe_allow_html=True)


def json_panel(title, data):
    glass_heading(title)
    st.code(json.dumps(data, indent=2, default=str), language="json")


def render_attempts(attempts):
    if not attempts:
        st.markdown('<div class="empty-state">No execution attempts have been recorded yet.</div>', unsafe_allow_html=True)
        return
    rows = []
    for index, attempt in enumerate(attempts, start=1):
        if isinstance(attempt, dict):
            rows.append({
                "#": index,
                "Action": attempt.get("action", attempt.get("name", "Unknown")),
                "Result": attempt.get("result", attempt.get("status", "Unknown")),
                "Verification": attempt.get("verification", attempt.get("verified", "—")),
            })
        else:
            rows.append({"#": index, "Action": str(attempt), "Result": "—", "Verification": "—"})
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_steps(steps):
    if not steps:
        st.markdown('<div class="empty-state">No explicit recovery steps were returned.</div>', unsafe_allow_html=True)
        return
    for index, step in enumerate(steps, start=1):
        st.markdown(f'''<div class="timeline-item"><div class="timeline-index">{index:02d}</div><div class="timeline-content">{html.escape(str(step))}</div></div>''', unsafe_allow_html=True)


def render_loop(loop):
    loop = loop or {}
    phase = loop.get("phase", "RECOVERY")
    status = loop.get("status", "UNKNOWN")
    attempts = loop.get("recoveryAttempts", 0)
    max_attempts = loop.get("maxAttempts", "—")
    verification = loop.get("verification")
    stages = [
        ("Intake", "Ticket mapped into a recovery session"),
        ("Evidence", "Historical evidence and approved runbooks evaluated"),
        ("Plan", "Recovery strategy selected and risk checked"),
        ("Approval", "Human decision required when policy demands it"),
        ("Verification", "Service state validated after execution"),
    ]
    current = {"RECOVERY": 2, "APPROVAL_GATE": 3, "VERIFIED_RECOVERY": 4, "ESCALATION": 4, "LOAD_FAILED": 0}.get(phase, 2)
    items = []
    for i, (name, description) in enumerate(stages):
        state = "complete" if i < current else "active" if i == current else "upcoming"
        items.append(f'<div class="pipeline-step {state}"><div class="pipeline-dot"></div><div><div class="pipeline-name">{name}</div><div class="pipeline-description">{description}</div></div></div>')
    st.markdown(f'''<div class="loop-summary"><div><span class="loop-key">Current phase</span><strong>{html.escape(str(phase).replace('_', ' '))}</strong></div><div><span class="loop-key">Attempts</span><strong>{html.escape(str(attempts))} / {html.escape(str(max_attempts))}</strong></div><div><span class="loop-key">Verification</span><strong>{html.escape(str(verification if verification is not None else 'Pending'))}</strong></div></div><div class="pipeline">{''.join(items)}</div>''', unsafe_allow_html=True)
    status_badge(status)
