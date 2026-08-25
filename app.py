import streamlit as st

from frontend.styles import inject_styles

from frontend.components import (
    glass_heading,
    json_panel,
    metric_card,
    render_attempts,
    render_steps,
    status_badge,
)

from frontend.controller import (
    approve_strategy,
    build_incident,
    reject_strategy,
    run_local_recovery,
    start_freshservice_recovery,
)


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="ReSolve",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "result": None,
    "active_ticket_id": None,
    "pending_session": None,
    "mode": "Freshservice",
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="resolve-kicker">
            Autonomous Recovery System
        </div>

        <div style="
            font-size: 1.7rem;
            font-weight: 700;
            letter-spacing: -0.04em;
            margin-top: 0.2rem;
        ">
            ReSolve
        </div>

        <div style="
            color: #8190a5;
            font-size: 0.8rem;
            margin-top: 0.35rem;
            line-height: 1.5;
        ">
            Organizational recovery memory for
            controlled agent remediation.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    mode = st.radio(
        "Recovery source",
        [
            "Freshservice",
            "Sandbox",
        ],
    )

    st.session_state.mode = mode

    st.divider()

    glass_heading("System")

    st.markdown(
        """
        <div class="status-pill status-online">
            BACKEND AVAILABLE
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.caption(
        "Recovery actions are evaluated through "
        "memory, policy and verification before "
        "terminal resolution."
    )


# =========================================================
# HEADER
# =========================================================

header_left, header_right = st.columns([7, 2])

with header_left:

    st.markdown(
        """
        <div class="resolve-kicker">
            INCIDENT RECOVERY CONSOLE
        </div>

        <div class="resolve-title">
            Controlled recovery, backed by memory.
        </div>

        <div class="resolve-subtitle">
            Inspect an incident, select a recovery path,
            and keep human approval in the loop when required.
        </div>
        """,
        unsafe_allow_html=True,
    )


with header_right:

    current_status = "READY"

    if st.session_state.result:
        current_status = st.session_state.result.get(
            "status",
            "UNKNOWN",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    status_badge(current_status)


st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# FRESHSERVICE MODE
# =========================================================

if mode == "Freshservice":

    tab_recovery, tab_result = st.tabs(
        [
            "Recovery",
            "Execution",
        ]
    )

    with tab_recovery:

        left, right = st.columns([1.15, 0.85])

        with left:

            st.markdown(
                '<div class="glass-card">',
                unsafe_allow_html=True,
            )

            glass_heading("Freshservice Incident")

            ticket_id = st.text_input(
                "Ticket ID",
                placeholder="e.g. 123",
            )

            first_action = st.text_area(
                "Initial action attempted",
                placeholder=(
                    "Describe the action already attempted "
                    "by the host agent."
                ),
                height=110,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            start = st.button(
                "Start Recovery",
                type="primary",
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-label">
                        Recovery Pipeline
                    </div>

                    <div style="
                        line-height: 2;
                        color: #b8c4d6;
                        font-size: 0.88rem;
                    ">
                        Freshservice ticket<br>
                        ↓<br>
                        Incident mapping<br>
                        ↓<br>
                        Recovery memory<br>
                        ↓<br>
                        Risk evaluation<br>
                        ↓<br>
                        Approval or execution<br>
                        ↓<br>
                        Verification
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if start:

            if not ticket_id.strip():

                st.error("A Freshservice ticket ID is required.")

            elif not first_action.strip():

                st.error(
                    "Describe the initial action attempted."
                )

            else:

                with st.spinner(
                    "Loading incident and starting recovery..."
                ):

                    try:

                        result = start_freshservice_recovery(
                            ticket_id.strip(),
                            first_action.strip(),
                        )

                        st.session_state.result = result
                        st.session_state.active_ticket_id = (
                            ticket_id.strip()
                        )

                        if result.get(
                            "status"
                        ) == "PENDING_APPROVAL":

                            st.session_state.pending_session = (
                                result.get("session")
                            )

                    except Exception as error:

                        st.session_state.result = {
                            "status": "ERROR",
                            "message": str(error),
                        }

                st.rerun()


    with tab_result:

        result = st.session_state.result

        if not result:

            st.info(
                "No Freshservice recovery has been started "
                "in this session."
            )

        else:

            render_result(
                result,
                freshservice=True,
            )


# =========================================================
# SANDBOX MODE
# =========================================================

else:

    tab_incident, tab_result = st.tabs(
        [
            "Incident",
            "Execution",
        ]
    )

    with tab_incident:

        with st.form("sandbox_incident_form"):

            st.markdown(
                '<div class="glass-card">',
                unsafe_allow_html=True,
            )

            glass_heading("Incident Context")

            col1, col2 = st.columns(2)

            with col1:

                title = st.text_input(
                    "Title",
                    value=(
                        "Database connection failures "
                        "causing payment API errors"
                    ),
                )

                service = st.text_input(
                    "Service",
                    value="Payments API",
                )

                environment = st.selectbox(
                    "Environment",
                    [
                        "production",
                        "staging",
                        "development",
                    ],
                )

                severity = st.selectbox(
                    "Severity",
                    [
                        "critical",
                        "high",
                        "medium",
                        "low",
                    ],
                    index=1,
                )

            with col2:

                api_latency = st.number_input(
                    "API latency (ms)",
                    min_value=0,
                    value=4200,
                )

                database_cpu = st.number_input(
                    "Database CPU (%)",
                    min_value=0,
                    max_value=100,
                    value=88,
                )

                change_minutes = st.number_input(
                    "Minutes before incident",
                    min_value=0,
                    value=20,
                )

            symptoms = st.text_area(
                "Symptoms",
                value=(
                    "Payment requests failing\n"
                    "Database connections timing out\n"
                    "High API response time"
                ),
            )

            error_codes = st.text_area(
                "Error codes",
                value="DB_CONNECTION_TIMEOUT",
            )

            change_col1, change_col2 = st.columns(2)

            with change_col1:

                change_type = st.text_input(
                    "Recent change type",
                    value="deployment",
                )

            with change_col2:

                change_description = st.text_input(
                    "Recent change description",
                    value=(
                        "Traffic increased after deployment"
                    ),
                )

            st.markdown("<hr>", unsafe_allow_html=True)

            glass_heading("Initial Recovery")

            first_action = st.text_input(
                "Action attempted",
                value="Restart read replica",
            )

            retry_result = st.selectbox(
                "Sandbox execution result",
                [
                    "success",
                    "failed",
                ],
            )

            submitted = st.form_submit_button(
                "Run Recovery",
                type="primary",
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        if submitted:

            if not title.strip() or not first_action.strip():

                st.error(
                    "Title and recovery action are required."
                )

            else:

                incident = build_incident(
                    title=title,
                    service=service,
                    environment=environment,
                    severity=severity,
                    symptoms=symptoms,
                    error_codes=error_codes,
                    api_latency=api_latency,
                    database_cpu=database_cpu,
                    change_type=change_type,
                    change_description=change_description,
                    change_minutes=change_minutes,
                )

                with st.spinner(
                    "Running recovery reasoning..."
                ):

                    try:

                        result = run_local_recovery(
                            incident,
                            first_action,
                            retry_result,
                        )

                        result["incident"] = incident

                        st.session_state.result = result

                    except Exception as error:

                        st.session_state.result = {
                            "status": "ERROR",
                            "message": str(error),
                            "incident": incident,
                        }

                st.rerun()


    with tab_result:

        result = st.session_state.result

        if not result:

            st.info(
                "Configure an incident and run the recovery "
                "pipeline."
            )

        else:

            render_result(
                result,
                freshservice=False,
            )


# =========================================================
# RESULT RENDERER
# =========================================================

def render_result(result, freshservice=False):

    status = result.get(
        "status",
        "UNKNOWN",
    )

    # -----------------------------------------------------
    # Top metrics
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        metric_card(
            "STATUS",
            status,
        )

    with col2:

        metric_card(
            "RECOVERY SCORE",
            (
                f"{result['score']:.3f}"
                if isinstance(
                    result.get("score"),
                    (int, float),
                )
                else "—"
            ),
        )

    with col3:

        metric_card(
            "ATTEMPTS",
            result.get(
                "recoveryAttempts",
                len(result.get("attempts", [])),
            ),
        )

    with col4:

        metric_card(
            "SOURCE",
            (
                result.get("freshserviceTicketId")
                if freshservice
                else result.get(
                    "sourceIncident",
                    "Sandbox",
                )
            ),
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Main result
    # -----------------------------------------------------

    if result.get("message"):

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        glass_heading("System Message")

        st.write(result["message"])

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Approval state
    # -----------------------------------------------------

    if status == "PENDING_APPROVAL":

        st.warning(
            "Recovery is paused pending human approval."
        )

        ticket_id = st.session_state.active_ticket_id
        session = result.get(
            "session",
            st.session_state.pending_session,
        )

        approve_col, reject_col = st.columns(2)

        with approve_col:

            if st.button(
                "Approve Strategy",
                type="primary",
            ):

                try:

                    with st.spinner(
                        "Continuing approved recovery..."
                    ):

                        new_result = approve_strategy(
                            ticket_id,
                            session,
                        )

                    st.session_state.result = new_result

                    st.rerun()

                except Exception as error:

                    st.error(str(error))

        with reject_col:

            if st.button(
                "Reject Strategy"
            ):

                try:

                    with st.spinner(
                        "Selecting another recovery path..."
                    ):

                        new_result = reject_strategy(
                            ticket_id,
                            session,
                        )

                    st.session_state.result = new_result

                    st.rerun()

                except Exception as error:

                    st.error(str(error))

        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Recovery action
    # -----------------------------------------------------

    if result.get("recoveryAction"):

        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True,
        )

        glass_heading("Selected Recovery Action")

        st.code(
            result["recoveryAction"],
            language="text",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Recovery steps
    # -----------------------------------------------------

    if result.get("steps"):

        glass_heading("Recovery Plan")

        render_steps(
            result["steps"]
        )

        st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Attempts
    # -----------------------------------------------------

    glass_heading("Execution History")

    render_attempts(
        result.get("attempts", [])
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Incident
    # -----------------------------------------------------

    incident = result.get("incident")

    if incident:

        with st.expander(
            "Incident Context",
            expanded=False,
        ):

            json_panel(
                "Mapped Incident",
                incident,
            )

    # -----------------------------------------------------
    # Raw result
    # -----------------------------------------------------

    with st.expander(
        "Raw Recovery Result",
        expanded=False,
    ):

        json_panel(
            "Backend Response",
            result,
        )