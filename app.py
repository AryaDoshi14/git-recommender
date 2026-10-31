"""GitFlix - GitHub, but Netflix.

Entry point for the Streamlit application.
Coordinates page configuration, CSS injection, navbar, session state switching,
and presentation state dispatching (welcome, loading, error, and results).
"""

import streamlit as st

from core.errors import GitHubError
from core.orchestrator import load_profile
from ui.components import (
    render_cold_start_banner,
    render_empty_state,
    render_error_state,
    render_footer,
    render_hero,
    render_navbar,
    render_recommendation_row,
    render_skeleton,
    render_welcome,
    show_rate_limit_toast,
)
from ui.styles import STYLES_CSS

# 1. Page Configuration
st.set_page_config(
    page_title="GitFlix: GitHub, but Netflix",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Inject Netflix-Style CSS
st.markdown(STYLES_CSS, unsafe_allow_html=True)

# 3. Session State Initialization
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "profile_data" not in st.session_state:
    st.session_state["profile_data"] = None
if "error_message" not in st.session_state:
    st.session_state["error_message"] = None

# 4. Top Navigation Bar
current_query = st.session_state.get("username", "")
searched_username = render_navbar(default_value=current_query)

# Handle search submission
if searched_username and searched_username.strip() != st.session_state.get("username", ""):
    st.session_state["username"] = searched_username.strip()
    st.session_state["profile_data"] = None
    st.session_state["error_message"] = None
    st.rerun()

active_user = st.session_state.get("username", "").strip()

# 5. State Switching
if not active_user:
    # State: Welcome Screen
    render_welcome()
    render_footer()

elif st.session_state.get("error_message"):
    # State: Error Screen
    render_error_state(st.session_state["error_message"])
    render_footer()

elif st.session_state.get("profile_data") is not None:
    # State: Results Loaded
    data = st.session_state["profile_data"]
    user = data.get("user", {})
    languages = data.get("languages", {})
    rows = data.get("rows", [])
    cold_start = data.get("cold_start", False)

    # Hero profile banner
    render_hero(user, languages)

    # Cold start notification if applicable
    if cold_start:
        render_cold_start_banner()

    # Recommendations rows or empty state
    if not rows:
        render_empty_state()
    else:
        for row in rows:
            render_recommendation_row(row.get("title", "Recommended"), row.get("repos", []))

    render_footer()

else:
    # State: Loading Profile (Skeleton)
    placeholder = st.empty()
    placeholder.markdown(render_skeleton(), unsafe_allow_html=True)

    try:
        data = load_profile(active_user)
        st.session_state["profile_data"] = data
        st.session_state["error_message"] = None
        placeholder.empty()
        st.rerun()

    except GitHubError as err:
        placeholder.empty()
        # Map error statuses to user-friendly messages
        if err.status == 404:
            st.session_state["error_message"] = "GitHub user not found. Please check the spelling."
        elif err.status in (403, 429):
            show_rate_limit_toast()
            st.session_state["error_message"] = (
                "GitHub API rate limit exceeded. Please wait a few minutes or configure a personal GITHUB_TOKEN."
            )
        elif err.status == 408:
            st.session_state["error_message"] = (
                "Request timed out, heavy profiles may need a second attempt."
            )
        else:
            st.session_state["error_message"] = err.message or "An unexpected GitHub API error occurred."
        st.rerun()

    except Exception as exc:
        placeholder.empty()
        st.session_state["error_message"] = (
            f"An unexpected error occurred: {str(exc)}"
        )
        st.rerun()
