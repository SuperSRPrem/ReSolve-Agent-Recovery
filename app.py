import streamlit as st
from datetime import datetime, time

from frontend.styles import inject_styles
from frontend.components import glass_heading, json_panel, metric_card, render_attempts, render_loop, render_steps, status_badge
from frontend.controller import approve_run, build_incident, reject_run, run_local_recovery, start_manual_recovery, start_ticket_recovery

st.set_page_config(page_title="ReSolve", page_icon=None, layout="wide", initial_sidebar_state="expanded")
inject_styles()

for key, value in {
    "result": None, "mode": "Recovery", "active_run_id": None, "active_ticket_id": None,
}.items():
    st.session_state.setdefault(key, value)


def render_result(result, freshservice=False):
    if not result:
        st.markdown('<div class="glass-card"><div class="empty-state">No recovery run is active. Start with an existing Freshservice ticket or create a manual incident.</div></div>', unsafe_allow_html=True)
        return
    status = result.get("status", "UNKNOWN")
    loop = result.get("loop", {})
    cols = st.columns(4)
    with cols[0]: metric_card("Status", status)
    with cols[1]: metric_card("Phase", loop.get("phase", "RECOVERY").replace("_", " "))
    with cols[2]: metric_card("Attempts", result.get("recoveryAttempts", len(result.get("attempts", []))))
    with cols[3]: metric_card("Ticket", result.get("freshserviceTicketId") or st.session_state.active_ticket_id or "Sandbox")
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1.2, .8])
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        glass_heading("Recovery progress")
        render_loop(loop if freshservice else {"status": status, "phase": "RECOVERY", "recoveryAttempts": result.get("recoveryAttempts", 0), "maxAttempts": 5, "verification": result.get("verification")})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        glass_heading("Current decision")
        if status == "AWAITING_APPROVAL":
            strategy = loop.get("pendingStrategy") or result.get("strategy") or {}
            action = strategy.get("action") if isinstance(strategy, dict) else str(strategy)
            risk = strategy.get("riskTier", "Policy controlled") if isinstance(strategy, dict) else "Policy controlled"
            st.markdown(f'<div class="approval-card"><div class="approval-title">Approval required</div><div class="muted">Proposed action: {action or "Selected recovery strategy"}<br>Risk: {risk}</div></div>', unsafe_allow_html=True)
            yes, no = st.columns(2)
            run_id = result.get("runId") or st.session_state.active_run_id
            with yes:
                if st.button("Yes, continue", type="primary", key="approve_run"):
                    try:
                        with st.spinner("Executing approved strategy..."):
                            new_result = approve_run(run_id)
                        st.session_state.result = new_result; st.session_state.active_run_id = new_result.get("runId", run_id); st.rerun()
                    except Exception as error: st.error(str(error))
            with no:
                if st.button("No, choose another", key="reject_run"):
                    try:
                        with st.spinner("Selecting another recovery path..."):
                            new_result = reject_run(run_id)
                        st.session_state.result = new_result; st.session_state.active_run_id = new_result.get("runId", run_id); st.rerun()
                    except Exception as error: st.error(str(error))
        elif result.get("message"):
            st.write(result["message"])
        else:
            st.markdown('<div class="empty-state">No human decision is required at this stage.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    if result.get("recoveryAction"):
        st.markdown("<br>", unsafe_allow_html=True); glass_heading("Selected recovery action"); st.code(result["recoveryAction"], language="text")
    if result.get("steps"):
        st.markdown("<br>", unsafe_allow_html=True); glass_heading("Recovery plan"); render_steps(result["steps"])
    st.markdown("<br>", unsafe_allow_html=True); glass_heading("Execution history"); render_attempts(result.get("attempts", []))
    if result.get("incident"):
        with st.expander("Incident context", expanded=False): json_panel("Mapped incident", result["incident"])
    with st.expander("Backend response", expanded=False): json_panel("Recovery result", result)


with st.sidebar:
    st.markdown('''<div class="resolve-kicker">Incident recovery system</div><div class="resolve-brand">ReSolve</div><div class="resolve-subtitle">Controlled remediation built around evidence, policy and verification.</div>''', unsafe_allow_html=True)
    st.divider()
    st.session_state.mode = st.radio("Workspace", ["Recovery", "Sandbox"], label_visibility="collapsed")
    st.divider()
    glass_heading("System")
    status_badge("BACKEND READY")
    st.caption("Freshservice incidents and manual intake converge into the same recovery loop.")

left, right = st.columns([7, 2])
with left:
    st.markdown('''<div class="resolve-kicker">Incident operations</div><div class="resolve-title">A controlled path from incident to verified recovery.</div><div class="resolve-subtitle">Create a Freshservice-aligned incident, recover an existing ticket, or inspect each stage of the active remediation run.</div>''', unsafe_allow_html=True)
with right:
    st.markdown("<br>", unsafe_allow_html=True)
    status_badge((st.session_state.result or {}).get("status", "READY"))
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.mode == "Recovery":
    tab_ticket, tab_manual, tab_execution = st.tabs(["Existing Ticket", "Manual Incident", "Recovery Loop"])

    with tab_ticket:
        a, b = st.columns([1.1, .9])
        with a:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            glass_heading("Recover an existing incident", "Enter the Freshservice ticket number. ReSolve fetches the ticket and uses available history rather than asking you to repeat prior actions.")
            with st.form("ticket_recovery_form"):
                ticket_id = st.text_input("Ticket number", placeholder="e.g. 123")
                submitted = st.form_submit_button("Start recovery", type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
            if submitted:
                if not ticket_id.strip():
                    st.error("A Freshservice ticket number is required.")
                else:
                    with st.spinner("Loading ticket and starting recovery..."):
                        try:
                            result = start_ticket_recovery(ticket_id.strip())
                            st.session_state.result = result
                            st.session_state.active_ticket_id = ticket_id.strip()
                            st.session_state.active_run_id = result.get("runId")
                            st.rerun()
                        except Exception as error:
                            st.session_state.result = {"status": "ERROR", "message": str(error)}
                            st.rerun()
        with b:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            glass_heading("What happens next")
            render_loop({"status": "READY", "phase": "RECOVERY", "recoveryAttempts": 0, "maxAttempts": 5})
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_manual:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        glass_heading("Manual incident intake", "Required fields are marked. Optional Freshservice-style fields are omitted from the ticket payload when left empty.")
        with st.form("manual_incident_form"):
            req1, req2 = st.columns(2)
            with req1: requester_email = st.text_input("Requester email *", placeholder="name@company.com")
            with req2: requester_id = st.text_input("Requester ID", placeholder="Optional when email is used")
            subject = st.text_input("Subject *")
            source = st.selectbox("Source", ["Phone", "Email", "Portal", "Chat"], index=0)
            status = st.selectbox("Status *", ["Open", "Pending", "Resolved", "Closed"], index=0)
            priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Urgent"], index=0)
            urgency, impact = st.columns(2)
            with urgency: urgency_value = st.selectbox("Urgency", ["Low", "Medium", "High"], index=0)
            with impact: impact_value = st.selectbox("Impact", ["Low", "Medium", "High"], index=0)
            category, sub_category = st.columns(2)
            with category: category_value = st.text_input("Category")
            with sub_category: sub_category_value = st.text_input("Sub-category")
            group, agent = st.columns(2)
            with group: group_id = st.text_input("Group ID")
            with agent: agent_id = st.text_input("Agent ID")
            department_id = st.text_input("Department ID")
            st.markdown("<div class='form-note'>Planning fields are optional.</div>", unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1: planned_start_date = st.date_input("Planned start date", value=None)
            with d2: planned_end_date = st.date_input("Planned end date", value=None)
            with d3: planned_effort = st.text_input("Planned effort", placeholder="e.g. 1h 10m")
            tags_text = st.text_input("Tags", placeholder="database, production")
            description = st.text_area("Description *", height=180)
            uploaded = st.file_uploader("Attachments", accept_multiple_files=True, help="The current MCP ticket path does not yet upload attachments; selected files are not sent until that backend capability is added.")
            submitted = st.form_submit_button("Create incident and start recovery", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
        if submitted:
            source_map = {"Email": 1, "Portal": 2, "Phone": 3, "Chat": 4}
            status_map = {"Open": 2, "Pending": 3, "Resolved": 4, "Closed": 5}
            priority_map = {"Low": 1, "Medium": 2, "High": 3, "Urgent": 4}
            level_map = {"Low": 1, "Medium": 2, "High": 3}
            form = {
                "requester_email": requester_email, "requester_id": requester_id,
                "subject": subject, "description": description,
                "source": source_map[source], "status": status_map[status], "priority": priority_map[priority],
                "urgency": level_map[urgency_value], "impact": level_map[impact_value],
                "category": category_value, "sub_category": sub_category_value,
                "group_id": group_id, "agent_id": agent_id, "department_id": department_id,
                "planned_start_date": planned_start_date.isoformat() if planned_start_date else None,
                "planned_end_date": planned_end_date.isoformat() if planned_end_date else None,
                "planned_effort": planned_effort,
                "tags": [x.strip() for x in tags_text.split(",") if x.strip()],
            }
            with st.spinner("Creating Freshservice incident and starting recovery..."):
                try:
                    result = start_manual_recovery(form)
                    st.session_state.result = result
                    st.session_state.active_ticket_id = result.get("freshserviceTicketId")
                    st.session_state.active_run_id = result.get("runId")
                    st.rerun()
                except Exception as error:
                    st.session_state.result = {"status": "ERROR", "message": str(error)}
                    st.rerun()

    with tab_execution:
        render_result(st.session_state.result, freshservice=True)

else:
    tab_incident, tab_execution = st.tabs(["Incident", "Recovery Loop"])
    with tab_incident:
        with st.form("sandbox_incident_form"):
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            glass_heading("Sandbox incident", "Use this isolated path to demonstrate the recovery engine without Freshservice.")
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Title", value="Database connection failures causing payment API errors")
                service = st.text_input("Service", value="Payments API")
                environment = st.selectbox("Environment", ["production", "staging", "development"])
                severity = st.selectbox("Severity", ["critical", "high", "medium", "low"], index=1)
            with c2:
                api_latency = st.number_input("API latency (ms)", min_value=0, value=4200)
                database_cpu = st.number_input("Database CPU (%)", min_value=0, max_value=100, value=88)
                change_minutes = st.number_input("Minutes before incident", min_value=0, value=20)
            symptoms = st.text_area("Symptoms", value="Payment requests failing\nDatabase connections timing out\nHigh API response time")
            error_codes = st.text_area("Error codes", value="DB_CONNECTION_TIMEOUT")
            x1, x2 = st.columns(2)
            with x1: change_type = st.text_input("Recent change type", value="deployment")
            with x2: change_description = st.text_input("Recent change description", value="Traffic increased after deployment")
            first_action = st.text_input("Action attempted", value="Restart read replica")
            retry_result = st.selectbox("Sandbox execution result", ["success", "failed"])
            submitted = st.form_submit_button("Run recovery", type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
        if submitted:
            incident = build_incident(title, service, environment, severity, symptoms, error_codes, api_latency, database_cpu, change_type, change_description, change_minutes)
            try:
                result = run_local_recovery(incident, first_action, retry_result)
                result["incident"] = incident
                st.session_state.result = result
                st.rerun()
            except Exception as error:
                st.session_state.result = {"status": "ERROR", "message": str(error), "incident": incident}
                st.rerun()

