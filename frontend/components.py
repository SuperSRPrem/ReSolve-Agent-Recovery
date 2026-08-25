import json
import streamlit as st


def status_class(status: str) -> str:
    status = (status or "").upper()

    if status in {"RECOVERED", "SUCCESS", "HEALTHY"}:
        return "status-online"

    if status in {
        "PENDING_APPROVAL",
        "PAUSED",
        "IN_PROGRESS",
        "RUNNING",
    }:
        return "status-warning"

    if status in {
        "FAILED",
        "ESCALATED",
        "LOAD_FAILED",
    }:
        return "status-danger"

    return "status-warning"


def status_badge(status: str):
    st.markdown(
        f"""
        <span class="status-pill {status_class(status)}">
            {status or "UNKNOWN"}
        </span>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def glass_heading(label):
    st.markdown(
        f"""
        <div class="section-label">{label}</div>
        """,
        unsafe_allow_html=True,
    )


def json_panel(title, data):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    glass_heading(title)

    st.code(
        json.dumps(
            data,
            indent=2,
            default=str,
        ),
        language="json",
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_attempts(attempts):
    if not attempts:
        st.caption("No recovery attempts recorded yet.")
        return

    rows = []

    for index, attempt in enumerate(attempts, start=1):

        if isinstance(attempt, dict):

            rows.append(
                {
                    "#": index,
                    "Action": attempt.get(
                        "action",
                        attempt.get("name", "Unknown"),
                    ),
                    "Result": attempt.get(
                        "result",
                        attempt.get("status", "Unknown"),
                    ),
                    "Verification": attempt.get(
                        "verification",
                        attempt.get("verified", "—"),
                    ),
                }
            )

        else:

            rows.append(
                {
                    "#": index,
                    "Action": str(attempt),
                    "Result": "—",
                    "Verification": "—",
                }
            )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


def render_steps(steps):

    if not steps:
        st.caption("No recovery steps were returned.")
        return

    for index, step in enumerate(steps, start=1):

        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom: 0.6rem;">
                <div class="section-label">
                    STEP {index:02d}
                </div>
                <div>{step}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )