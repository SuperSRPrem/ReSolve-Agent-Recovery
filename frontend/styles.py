def inject_styles():
    import streamlit as st

    st.markdown(
        """
        <style>

        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --bg: #07111f;
            --bg-secondary: #0b1626;

            --panel: rgba(15, 27, 45, 0.58);
            --panel-hover: rgba(21, 37, 60, 0.72);

            --border: rgba(148, 163, 184, 0.15);
            --border-bright: rgba(148, 163, 184, 0.28);

            --text: #edf3ff;
            --muted: #8190a5;

            --blue: #61a5ff;
            --cyan: #56d6ff;

            --green: #42d392;
            --amber: #e7b55a;
            --red: #f26b7a;

            --mono: 'DM Mono', monospace;
            --sans: 'Inter', sans-serif;
        }

        html, body, [class*="css"] {
            font-family: var(--sans);
        }

        .stApp {
            background:
                radial-gradient(
                    circle at 10% 0%,
                    rgba(38, 99, 235, 0.13),
                    transparent 32%
                ),
                radial-gradient(
                    circle at 90% 10%,
                    rgba(6, 182, 212, 0.08),
                    transparent 30%
                ),
                linear-gradient(
                    180deg,
                    #07111f 0%,
                    #081321 100%
                );
            color: var(--text);
        }

        #MainMenu,
        footer,
        header {
            visibility: hidden;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        /* Sidebar */

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    rgba(9, 20, 35, 0.98),
                    rgba(5, 13, 24, 0.98)
                );
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        /* Typography */

        .resolve-kicker {
            font-family: var(--mono);
            font-size: 0.7rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--blue);
        }

        .resolve-title {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.04em;
            margin: 0.15rem 0;
        }

        .resolve-subtitle {
            color: var(--muted);
            font-size: 0.92rem;
        }

        /* Glass panels */

        .glass-card {
            background: var(--panel);
            border: 1px solid var(--border);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-radius: 18px;
            padding: 1.15rem 1.25rem;
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.14),
                inset 0 1px 0 rgba(255,255,255,0.025);
        }

        .glass-card:hover {
            border-color: var(--border-bright);
        }

        .section-label {
            font-family: var(--mono);
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.85rem;
        }

        /* Metric cards */

        .metric-card {
            min-height: 110px;
            padding: 1rem 1.1rem;
            border-radius: 16px;

            background:
                linear-gradient(
                    145deg,
                    rgba(24, 40, 64, 0.72),
                    rgba(11, 21, 37, 0.55)
                );

            border: 1px solid var(--border);

            backdrop-filter: blur(18px);
        }

        .metric-label {
            font-family: var(--mono);
            color: var(--muted);
            font-size: 0.67rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .metric-value {
            font-size: 1.65rem;
            font-weight: 600;
            margin-top: 0.45rem;
            color: var(--text);
        }

        /* Status */

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;

            font-family: var(--mono);
            font-size: 0.72rem;
            letter-spacing: 0.04em;

            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            border: 1px solid;
        }

        .status-online {
            color: var(--green);
            background: rgba(66, 211, 146, 0.08);
            border-color: rgba(66, 211, 146, 0.25);
        }

        .status-warning {
            color: var(--amber);
            background: rgba(231, 181, 90, 0.08);
            border-color: rgba(231, 181, 90, 0.25);
        }

        .status-danger {
            color: var(--red);
            background: rgba(242, 107, 122, 0.08);
            border-color: rgba(242, 107, 122, 0.25);
        }

        /* Streamlit inputs */

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(6, 15, 27, 0.55) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            border-radius: 10px !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: rgba(97, 165, 255, 0.7) !important;
            box-shadow: 0 0 0 1px rgba(97, 165, 255, 0.2) !important;
        }

        /* Buttons */

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid rgba(97, 165, 255, 0.32);

            background:
                linear-gradient(
                    135deg,
                    rgba(37, 99, 235, 0.88),
                    rgba(29, 78, 216, 0.88)
                );

            color: white;
            font-weight: 600;

            padding: 0.58rem 1rem;

            transition:
                transform 0.15s ease,
                box-shadow 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);

            box-shadow:
                0 8px 24px rgba(37, 99, 235, 0.22);
        }

        /* Tabs */

        .stTabs [data-baseweb="tab-list"] {
            gap: 1.6rem;
            border-bottom: 1px solid var(--border);
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--muted);
            padding-left: 0;
            padding-right: 0;
        }

        .stTabs [aria-selected="true"] {
            color: var(--text);
        }

        /* Expanders */

        .streamlit-expanderHeader {
            background: rgba(15, 27, 45, 0.5);
            border-radius: 10px;
        }

        /* JSON */

        pre {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )