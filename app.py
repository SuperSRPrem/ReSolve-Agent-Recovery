import streamlit as st

from backend.demo_agent import DemoAgent


st.set_page_config(
    page_title="Recovery Memory",
    layout="wide"
)

st.title("Recovery Memory")
st.write("Reusable recovery memory for failed agent actions")

st.subheader("Current Incident")

with st.form("incidentForm"):
    title = st.text_input(
        "Title",
        "Database connection failures causing payment API errors"
    )

    service = st.text_input(
        "Service",
        "Payments API"
    )

    environment = st.text_input(
        "Environment",
        "production"
    )

    severity = st.text_input(
        "Severity",
        "high"
    )

    symptomsText = st.text_area(
        "Symptoms - one per line",
        "Payment requests failing\nDatabase connections timing out\nHigh API response time"
    )

    codesText = st.text_area(
        "Error codes - one per line",
        "DB_CONNECTION_TIMEOUT"
    )

    apiLatency = st.number_input(
        "API latency in ms",
        min_value=0,
        value=4200
    )

    databaseCpu = st.number_input(
        "Database CPU percent",
        min_value=0,
        max_value=100,
        value=88
    )

    changeType = st.text_input(
        "Recent change type",
        "deployment"
    )

    changeDesc = st.text_input(
        "Recent change description",
        "Traffic increased after deployment"
    )

    changeMins = st.number_input(
        "Minutes before incident",
        min_value=0,
        value=20
    )

    firstAction = st.text_input(
        "First action attempted",
        "Restart read replica"
    )

    retryResult = st.selectbox(
        "Simulated recovery result",
        ["success", "failed"]
    )

    runDemo = st.form_submit_button("Run Recovery")


if runDemo:
    symptoms = [
        item.strip()
        for item in symptomsText.splitlines()
        if item.strip()
    ]

    errorCodes = [
        item.strip()
        for item in codesText.splitlines()
        if item.strip()
    ]

    currentIncident = {
        "title": title,
        "service": service,
        "environment": environment,
        "severity": severity,
        "symptoms": symptoms,
        "errorCodes": errorCodes,
        "metrics": {
            "apiLatencyMs": apiLatency,
            "databaseCpuPercent": databaseCpu
        },
        "recentChange": {
            "type": changeType,
            "description": changeDesc,
            "minutesBeforeIncident": changeMins
        },
        "actionsTried": []
    }

    if not title.strip() or not firstAction.strip():
        st.error("Title and first action are required.")
    else:
        agent = DemoAgent()

        result = agent.runIncident(
            currentIncident,
            firstAction,
            retryResult
        )

        st.divider()

        st.subheader("Current Incident")

        st.json(currentIncident)

        st.subheader("Agent Flow")

        st.write("**1. Host agent action**")
        st.write(firstAction)

        st.error("Action failed")

        st.write("**2. Recovery Memory lookup**")

        if result["status"] == "NO_MATCH":
            st.warning(result["message"])

            st.subheader("Attempts")
            st.dataframe(
                result["attempts"],
                use_container_width=True
            )

        else:
            st.write("Historical recovery found")

            st.write("**3. Recovery action**")
            st.write(result["recoveryAction"])

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Source incident",
                    result["sourceIncident"]
                )

            with col2:
                st.metric(
                    "Recovery score",
                    f'{result["score"]:.3f}'
                )

            st.write("**Recovery steps**")

            for number, step in enumerate(
                result["steps"],
                start=1
            ):
                st.write(f"{number}. {step}")

            st.write("**4. Recovery evaluation**")

            if result["status"] == "RECOVERED":
                st.success("Recovery succeeded")
            else:
                st.error("Recovery failed")

            st.subheader("Attempts")

            st.dataframe(
                result["attempts"],
                use_container_width=True
            )
