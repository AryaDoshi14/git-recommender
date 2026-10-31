"""UI presentation components for GitFlix.

Contains only presentation and HTML layout logic with complete HTML escaping.
Does NOT import or call GitHub or API logic.
"""

from datetime import datetime
import html
import textwrap
from typing import Any, Dict, List, Optional
import streamlit as st

from ui.colors import get_language_color


def format_stars(count: int) -> str:
    """Format repository star count into compact readable string (e.g., 1.2k, 450)."""
    if not isinstance(count, (int, float)) or count < 0:
        return "0"
    if count >= 1000:
        val = count / 1000.0
        return f"{val:.1f}k".replace(".0k", "k")
    return str(int(count))


def render_navbar(default_value: str = "") -> Optional[str]:
    """Render the top navbar with GitFlix branding and pill-shaped search input form."""
    col_logo, col_form = st.columns([1, 2])

    with col_logo:
        st.markdown(
            '<div class="logo-wrapper">'
            '<span class="gitflix-logo">🍿 GITFLIX</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    with col_form:
        with st.form(key="search_form", clear_on_submit=False):
            c_input, c_btn = st.columns([3.5, 1.2], vertical_alignment="center")
            username_input = c_input.text_input(
                label="GitHub Username",
                value=default_value,
                placeholder="Enter GitHub username...",
                label_visibility="collapsed",
            )
            submitted = c_btn.form_submit_button("Explore")
            if submitted and username_input:
                return username_input.strip()

    return None


def render_welcome() -> None:
    """Render the welcome introduction state when no username has been searched."""
    html_content = textwrap.dedent("""
    <div class="welcome-container">
        <div class="welcome-icon-box">🎬</div>
        <h1 class="welcome-headline">Welcome to GitFlix</h1>
        <p class="welcome-description">
            The personalized discovery engine for developers. Enter your GitHub username above
            to find your next great project to contribute to, star, or learn from.
        </p>
        <div class="feature-dots-container">
            <div class="feature-dot-item">
                <span class="feature-dot dot-purple"></span>
                <span>Vector Matching</span>
            </div>
            <div class="feature-dot-item">
                <span class="feature-dot dot-emerald"></span>
                <span>Hidden Gems</span>
            </div>
            <div class="feature-dot-item">
                <span class="feature-dot dot-blue"></span>
                <span>Smart Filters</span>
            </div>
        </div>
    </div>
    """).strip()
    st.markdown(html_content, unsafe_allow_html=True)


def render_skeleton() -> str:
    """Generate HTML for 3 rows of 4 pulsing placeholder cards with zero indentation."""
    rows_html = []
    for _ in range(3):
        cards_html = "".join(['<div class="skeleton-card"></div>' for _ in range(4)])
        rows_html.append(
            '<div class="skeleton-row">'
            '<div class="skeleton-title"></div>'
            f'<div class="skeleton-grid">{cards_html}</div>'
            '</div>'
        )
    return f'<div style="padding-top: 1.5rem;">{"".join(rows_html)}</div>'


def render_hero(user: Dict[str, Any], languages: Dict[str, float]) -> None:
    """Render the user profile hero banner with avatar, bio, and top 5 language pills."""
    avatar_url = html.escape(user.get("avatar_url") or "https://github.com/ghost.png")
    login = html.escape(user.get("login") or "Developer")
    name = html.escape(user.get("name") or "")
    display_name = f"{name} (@{login})" if name else f"@{login}"

    raw_bio = user.get("bio")
    bio_text = html.escape(raw_bio.strip()) if raw_bio and raw_bio.strip() else (
        "No bio provided. Just a passion for building cool stuff on GitHub."
    )

    # Build top 5 language pills
    pills_html = []
    for lang, pct in list(languages.items())[:5]:
        esc_lang = html.escape(str(lang))
        color = get_language_color(lang)
        pills_html.append(
            f'<span class="lang-pill">'
            f'<span class="lang-pill-dot" style="background-color: {color};"></span>'
            f'{esc_lang} {round(pct)}%'
            f'</span>'
        )

    pills_rendered = "".join(pills_html)

    html_content = textwrap.dedent(f"""
    <div class="hero-wrapper">
        <img src="{avatar_url}" alt="{login}" class="hero-avatar" />
        <div class="hero-name">{display_name}</div>
        <div class="hero-bio">{bio_text}</div>
        <div class="hero-pills">{pills_rendered}</div>
    </div>
    """).strip()
    st.markdown(html_content, unsafe_allow_html=True)


def render_cold_start_banner() -> None:
    """Render a notice for accounts with fewer than 5 starred repositories."""
    banner_html = textwrap.dedent("""
    <div class="cold-start-banner">
        <span style="font-size: 1.4rem;">💡</span>
        <span>
            <strong>Cold Start:</strong> It looks like you haven't starred many repositories yet!
            We've curated some trending and popular projects in your stack for you to explore.
        </span>
    </div>
    """).strip()
    st.markdown(banner_html, unsafe_allow_html=True)


def render_repo_card(repo: Dict[str, Any]) -> str:
    """Render a single 300-350px Netflix-style repository card as an HTML string."""
    raw_name = repo.get("name") or "untitled-repo"
    esc_name = html.escape(raw_name)

    raw_desc = repo.get("description")
    esc_desc = html.escape(raw_desc.strip()) if raw_desc and raw_desc.strip() else (
        "No description available for this repository."
    )

    raw_lang = repo.get("language") or "Unknown"
    esc_lang = html.escape(raw_lang.upper())
    lang_color = get_language_color(raw_lang)

    owner = repo.get("owner") or {}
    owner_login = html.escape(owner.get("login") or "")
    avatar_url = owner.get("avatar_url")

    if avatar_url:
        esc_avatar = html.escape(avatar_url)
        owner_html = f'<img src="{esc_avatar}" alt="{owner_login}" class="owner-img" />'
    else:
        initial = html.escape(owner_login[:1].upper() if owner_login else "?")
        owner_html = f'<div class="owner-fallback">{initial}</div>'

    stars = format_stars(repo.get("stargazers_count", 0))

    html_url = html.escape(repo.get("html_url") or f"https://github.com/{repo.get('full_name', '')}")

    return textwrap.dedent(f"""
    <div class="repo-card">
        <div>
            <div class="card-top">
                <span class="lang-badge">
                    <span style="width:7px; height:7px; border-radius:50%; background-color:{lang_color}; display:inline-block;"></span>
                    {esc_lang}
                </span>
                <div class="owner-pill">
                    {owner_html}
                </div>
            </div>
            <div class="card-title" title="{esc_name}">{esc_name}</div>
            <div class="card-desc" title="{esc_desc}">{esc_desc}</div>
        </div>
        <div class="card-bottom">
            <div class="star-count">
                <span class="star-icon">★</span>
                <span>{stars}</span>
            </div>
            <a href="{html_url}" target="_blank" rel="noopener noreferrer" class="gh-button">
                View on GitHub ↗
            </a>
        </div>
    </div>
    """).strip()


def render_recommendation_row(title: str, repos: List[Dict[str, Any]]) -> None:
    """Render a horizontally scrolling row with scroll-snap and fade edges."""
    if not repos:
        return

    esc_title = html.escape(title)
    cards_html = "".join([render_repo_card(repo) for repo in repos])

    row_html = (
        f'<div class="row-section">'
        f'<div class="row-title"><span>🍿</span><span>{esc_title}</span></div>'
        f'<div class="row-scroll-container">{cards_html}</div>'
        f'</div>'
    )
    st.markdown(row_html, unsafe_allow_html=True)


def render_empty_state() -> None:
    """Render an empty state when no recommendations could be generated."""
    html_content = textwrap.dedent("""
    <div class="empty-state">
        <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
        <h3>No recommendations found</h3>
        <p>Star more repositories on GitHub so our AI engine can learn your preferences and recommend matching projects!</p>
    </div>
    """).strip()
    st.markdown(html_content, unsafe_allow_html=True)


def render_error_state(message: str) -> None:
    """Render an error banner with a button to reset session state."""
    esc_msg = html.escape(message)
    error_html = textwrap.dedent(f"""
    <div class="error-banner">
        <div class="error-title">Search Failed</div>
        <div class="error-msg">{esc_msg}</div>
    </div>
    """).strip()
    st.markdown(error_html, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Try another username", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def show_rate_limit_toast() -> None:
    """Trigger a Streamlit toast for GitHub rate limit notifications."""
    st.toast("GitHub Rate Limit hit! Add a personal GITHUB_TOKEN to increase limits.", icon="⚠️")


def render_footer() -> None:
    """Render the bottom footer."""
    year = datetime.now().year
    footer_html = textwrap.dedent(f"""
    <div class="gitflix-footer">
        <div>Built with <span>Streamlit</span> & <span>OpenRouter</span></div>
        <div>© {year} GitFlix · Not affiliated with GitHub</div>
    </div>
    """).strip()
    st.markdown(footer_html, unsafe_allow_html=True)
