import json

import oracledb
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Ask Leitz | AI Product Advisor",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# LIGHTWEIGHT PROFESSIONAL STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* Hide Streamlit development chrome */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    /* Main application background */
    .stApp {
        background:
            radial-gradient(
                circle at 85% 0%,
                rgba(80, 105, 140, 0.10),
                transparent 32%
            ),
            #0b0f14;
    }

    /* Main content width */
    .block-container {
        max-width: 1450px;
        padding-top: 2.0rem;
        padding-bottom: 7rem;
    }

    /* Headings */
    h1 {
        letter-spacing: -0.035em;
    }

    h2, h3 {
        letter-spacing: -0.02em;
    }

    /* Bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.018);
        border-color: rgba(255,255,255,0.075) !important;
        border-radius: 14px !important;
    }

    /* Buttons */
    div[data-testid="stButton"] button {
        min-height: 52px;
        border-radius: 10px;
        background: #121821;
        border: 1px solid rgba(255,255,255,0.09);
        font-weight: 550;
        transition: 0.15s ease;
    }

    div[data-testid="stButton"] button:hover {
        background: #171f2a;
        border-color: rgba(190,205,225,0.30);
        transform: translateY(-1px);
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: rgba(17, 23, 32, 0.78);
        border: 1px solid rgba(255,255,255,0.065);
        border-radius: 14px;
        padding: 0.55rem 0.75rem;
        margin-bottom: 0.7rem;
    }

    [data-testid="stChatMessageContent"] {
        line-height: 1.65;
    }

    /* Chat input */
    [data-testid="stChatInput"] {
        background: #151a23;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
    }

    /* Captions */
    .stCaption {
        color: #8490a0;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.06);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIGURATION
# ============================================================

oracle = st.secrets["oracle"]
TEAM_NAME = st.secrets["agent"]["team_name"]

LLM_NAME = "Gemini 2.5 Flash"
EMBEDDING_MODEL = "LEITZ_TEXT_MODEL"
DATABASE_NAME = "Oracle AI Database 26ai"


# ============================================================
# DATABASE CONNECTION POOL
# ============================================================

@st.cache_resource
def create_pool():

    return oracledb.create_pool(
        user=oracle["user"],
        password=oracle["password"],
        dsn=oracle["dsn"],
        config_dir=oracle["wallet_dir"],
        wallet_location=oracle["wallet_dir"],
        wallet_password=oracle["wallet_password"],
        min=1,
        max=4,
        increment=1,
    )


pool = create_pool()


# ============================================================
# DATABASE HELPERS
# ============================================================

def read_value(value):

    if value is None:
        return ""

    if hasattr(value, "read"):
        return value.read()

    return str(value)


def get_tool_count():

    with pool.acquire() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM LEITZ_TOOLS
                """
            )

            return cursor.fetchone()[0]


def create_conversation():

    with pool.acquire() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT DBMS_CLOUD_AI.CREATE_CONVERSATION()
                FROM dual
                """
            )

            return read_value(
                cursor.fetchone()[0]
            )


def run_agent(question, conversation_id):

    params = json.dumps(
        {
            "conversation_id": conversation_id
        }
    )

    with pool.acquire() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT DBMS_CLOUD_AI_AGENT.RUN_TEAM(
                    :team_name,
                    :user_prompt,
                    :params
                )
                FROM dual
                """,
                {
                    "team_name": TEAM_NAME,
                    "user_prompt": question,
                    "params": params,
                },
            )

            result = cursor.fetchone()[0]

            return read_value(result)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

database_ok = False
product_count = 0
database_error = None

try:

    product_count = get_tool_count()
    database_ok = True

except Exception as exc:

    database_error = str(exc)


# ============================================================
# TOP HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1],
    vertical_alignment="center"
)

with header_left:

    st.title("Ask Leitz")

    st.caption(
        "AI Product Intelligence · Powered by Oracle AI Database 26ai"
    )


with header_right:

    if database_ok:
        st.success("● Agent online")
    else:
        st.error("● Offline")


st.divider()


# ============================================================
# APPLICATION LAYOUT
# ============================================================

main_col, info_col = st.columns(
    [3.4, 1.05],
    gap="large"
)


# ============================================================
# MAIN APPLICATION AREA
# ============================================================

with main_col:

    # --------------------------------------------------------
    # HERO — ONLY BEFORE FIRST MESSAGE
    # --------------------------------------------------------

    if not st.session_state.messages:

        st.caption(
            "ENGINEERING PRODUCT DISCOVERY"
        )

        st.header(
            "Find the right tool. Ask naturally."
        )

        st.markdown(
            """
            Ask technical questions in ordinary language.

            **Ask Leitz** combines exact engineering criteria with
            semantic AI Vector Search to identify the most relevant
            products from the catalog.
            """
        )

        st.write("")

        # ----------------------------------------------------
        # HOW IT WORKS
        # ----------------------------------------------------

        c1, c2, c3 = st.columns(3)

        with c1:

            with st.container(border=True):

                st.caption("01 · FILTER")

                st.subheader(
                    "Technical criteria"
                )

                st.write(
                    """
                    Diameter, material, geometry and product
                    type are applied as exact database filters.
                    """
                )


        with c2:

            with st.container(border=True):

                st.caption("02 · DISCOVER")

                st.subheader(
                    "Semantic search"
                )

                st.write(
                    """
                    Oracle AI Vector Search understands the
                    intended application, not just exact keywords.
                    """
                )


        with c3:

            with st.container(border=True):

                st.caption("03 · RECOMMEND")

                st.subheader(
                    "Agent intelligence"
                )

                st.write(
                    """
                    The agent selects the appropriate search
                    strategy and explains its recommendations.
                    """
                )


        st.write("")
        st.write("")

        # ----------------------------------------------------
        # EXAMPLE QUESTIONS
        # ----------------------------------------------------

        st.subheader(
            "Suggested questions"
        )

        st.caption(
            "Choose a common engineering scenario or enter your own request."
        )


        example_1 = (
            "Find carbide tools between 200 and 250 mm "
            "suitable for very clean hardwood furniture finishing."
        )

        example_2 = (
            "Which carbide tools between 200 and 250 mm "
            "are best for aggressive material removal from solid timber?"
        )

        example_3 = (
            "What carbide saw blades do we have "
            "and what are their main differences?"
        )


        e1, e2, e3 = st.columns(3)

        with e1:

            if st.button(
                "Clean furniture finishing",
                use_container_width=True
            ):
                st.session_state.quick_prompt = example_1


        with e2:

            if st.button(
                "High material removal",
                use_container_width=True
            ):
                st.session_state.quick_prompt = example_2


        with e3:

            if st.button(
                "Compare saw blades",
                use_container_width=True
            ):
                st.session_state.quick_prompt = example_3


        st.write("")
        st.write("")


    # --------------------------------------------------------
    # CONVERSATION HEADER
    # --------------------------------------------------------

    else:

        conversation_title, new_button = st.columns(
            [5, 1]
        )

        with conversation_title:

            st.subheader(
                "Product Advisor"
            )

            st.caption(
                "Continue the conversation or refine the previous recommendation."
            )


        with new_button:

            if st.button(
                "New search",
                use_container_width=True
            ):

                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.session_state.quick_prompt = None

                st.rerun()


        st.divider()


    # --------------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


# ============================================================
# INFORMATION PANEL
# ============================================================

with info_col:

    # --------------------------------------------------------
    # SYSTEM OVERVIEW
    # --------------------------------------------------------

    with st.container(
        border=True
    ):

        st.caption(
            "SYSTEM OVERVIEW"
        )

        st.metric(
            "Catalog products",
            product_count
        )

        st.divider()

        st.caption(
            "SEARCH"
        )

        st.markdown(
            "**Hybrid AI Search**"
        )

        st.caption(
            "Exact SQL filtering + semantic Vector Search"
        )

        st.write("")

        st.caption(
            "LANGUAGE MODEL"
        )

        st.markdown(
            f"**{LLM_NAME}**"
        )

        st.write("")

        st.caption(
            "DATABASE"
        )

        st.markdown(
            f"**{DATABASE_NAME}**"
        )


    st.write("")


    # --------------------------------------------------------
    # SEARCH PROCESS
    # --------------------------------------------------------

    with st.container(
        border=True
    ):

        st.caption(
            "SEARCH PROCESS"
        )

        st.markdown(
            """
            **1. Understand intent**

            Interpret the engineering requirement.

            **2. Apply constraints**

            Material, diameter, geometry and type.

            **3. Rank semantically**

            Compare product meaning using vectors.

            **4. Recommend**

            Explain the most relevant options.
            """
        )


    st.write("")


    # --------------------------------------------------------
    # TECHNICAL DETAILS
    # --------------------------------------------------------

    with st.expander(
        "Developer details"
    ):

        st.caption(
            "AGENT TEAM"
        )

        st.code(
            TEAM_NAME
        )

        st.caption(
            "EMBEDDING MODEL"
        )

        st.code(
            EMBEDDING_MODEL
        )

        st.caption(
            "CONVERSATION ID"
        )

        st.code(
            st.session_state.conversation_id
            or "Not started"
        )

        if database_error:

            st.caption(
                "DATABASE ERROR"
            )

            st.code(
                database_error
            )


# ============================================================
# CHAT INPUT
# ============================================================

typed_prompt = st.chat_input(
    "Describe a tool, material, geometry or application..."
)


prompt = typed_prompt


# Handle quick-question buttons
if (
    not prompt
    and st.session_state.quick_prompt
):

    prompt = st.session_state.quick_prompt

    st.session_state.quick_prompt = None


# ============================================================
# EXECUTE AGENT
# ============================================================

if prompt:

    # --------------------------------------------------------
    # Start Oracle conversation if necessary
    # --------------------------------------------------------

    if not st.session_state.conversation_id:

        try:

            st.session_state.conversation_id = (
                create_conversation()
            )

        except Exception as exc:

            st.error(
                "Could not create the Oracle AI conversation."
            )

            st.code(
                str(exc)
            )

            st.stop()


    # --------------------------------------------------------
    # Add user message
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )


    # --------------------------------------------------------
    # Show current user message
    # --------------------------------------------------------

    with main_col:

        with st.chat_message(
            "user"
        ):

            st.markdown(
                prompt
            )


        # ----------------------------------------------------
        # Agent response
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            try:

                with st.status(
                    "Analyzing product catalog...",
                    expanded=False
                ):

                    answer = run_agent(
                        prompt,
                        st.session_state.conversation_id
                    )


                st.markdown(
                    answer
                )


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )


            except Exception as exc:

                st.error(
                    "The Product Advisor could not complete the request."
                )

                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        str(exc)
                    )