"""CSS design system for GitFlix.

Single unified stylesheet providing Netflix-inspired aesthetics, dark theme,
custom scroll-snap horizontal rows, glowing cards, and skeleton animations.
"""

STYLES_CSS = """
<style>
/* -------------------------------------------------------------
   GitFlix Global Resets & Streamlit Overrides
   ------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: #0d0d0d !important;
    color: #ffffff;
}

/* Remove default Streamlit top padding and branding decoration */
.stApp {
    background-color: #0d0d0d;
}

/* Ensure Streamlit top header is transparent and non-intrusive */
header[data-testid="stHeader"],
[data-testid="stHeader"],
header {
    background-color: transparent !important;
    background: transparent !important;
    backdrop-filter: none !important;
    pointer-events: none !important;
    z-index: 50 !important;
}

header[data-testid="stHeader"] *,
[data-testid="stHeader"] * {
    pointer-events: auto !important;
}

footer {
    display: none !important;
}

/* Block container padding adjustments - ensure full clearance across all Streamlit versions */
.block-container,
[data-testid="block-container"],
[data-testid="stMainBlockContainer"],
.stMainBlockContainer,
section.main > div.block-container,
div[data-testid="stAppViewBlockContainer"] {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1350px !important;
    position: relative;
}

/* -------------------------------------------------------------
   Navbar & Search Input Styling (Always stays on top of overlays)
   ------------------------------------------------------------- */
.gitflix-nav-wrapper {
    position: relative;
    z-index: 9999 !important;
    width: 100%;
    margin-bottom: 1.5rem;
}

/* Prevent Streamlit loading/stale veil from dimming or hiding search bar */
[data-testid="stForm"],
[data-testid="stForm"] * {
    opacity: 1 !important;
    filter: none !important;
    pointer-events: auto !important;
}
.gitflix-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0 1.5rem 0;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.gitflix-logo {
    font-size: 2.2rem;
    font-weight: 900;
    letter-spacing: -0.05em;
    color: #7c3aed;
    text-transform: uppercase;
    text-shadow: 0 0 25px rgba(124, 58, 237, 0.45);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* Streamlit Search Form Overrides */
[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

div[data-testid="stTextInput"] input {
    background-color: #1a1a1a !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 9999px !important;
    color: #ffffff !important;
    padding: 0.65rem 1.4rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease-in-out;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 16px rgba(124, 58, 237, 0.35) !important;
    outline: none !important;
}

div[data-testid="stFormSubmitButton"] button {
    background-color: #7c3aed !important;
    color: #ffffff !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.75rem !important;
    border: none !important;
    transition: all 0.2s ease-in-out;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #6d28d9 !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
    transform: translateY(-1px);
}

/* -------------------------------------------------------------
   Welcome State Components
   ------------------------------------------------------------- */
.welcome-container {
    text-align: center;
    max-width: 780px;
    margin: 1.5rem auto 2rem auto;
    padding: 0.75rem 1.5rem;
}

.welcome-icon-box {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 72px;
    height: 72px;
    background: rgba(124, 58, 237, 0.15);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 20px;
    font-size: 2.2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 0 30px rgba(124, 58, 237, 0.25);
}

.welcome-headline {
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 40%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
}

.welcome-description {
    font-size: 1.15rem;
    line-height: 1.65;
    color: #9ca3af;
    margin-bottom: 2.5rem;
}

.feature-dots-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.feature-dot-item {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: #d1d5db;
}

.feature-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.dot-purple { background-color: #a855f7; box-shadow: 0 0 10px #a855f7; }
.dot-emerald { background-color: #10b981; box-shadow: 0 0 10px #10b981; }
.dot-blue { background-color: #3b82f6; box-shadow: 0 0 10px #3b82f6; }

/* -------------------------------------------------------------
   Hero Profile Section
   ------------------------------------------------------------- */
.hero-wrapper {
    position: relative;
    padding: 3rem 2rem;
    margin-bottom: 2.5rem;
    border-radius: 20px;
    background: radial-gradient(circle at 50% 20%, rgba(124, 58, 237, 0.16) 0%, rgba(26, 26, 26, 0.4) 65%, transparent 100%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.hero-avatar {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(124, 58, 237, 0.4);
    box-shadow: 0 0 35px rgba(124, 58, 237, 0.35);
    margin-bottom: 1.25rem;
}

.hero-name {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #ffffff 60%, #c4b5fd 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.hero-bio {
    max-width: 650px;
    font-size: 1.05rem;
    color: #9ca3af;
    line-height: 1.55;
    margin-bottom: 1.5rem;
}

.hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
}

.lang-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.35rem 0.85rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #e5e7eb;
}

.lang-pill-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

/* -------------------------------------------------------------
   Cold-Start & State Banners
   ------------------------------------------------------------- */
.cold-start-banner {
    background: linear-gradient(90deg, rgba(124, 58, 237, 0.15) 0%, rgba(31, 31, 31, 0.6) 100%);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 12px;
    padding: 1.1rem 1.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    color: #e2e8f0;
    font-size: 0.95rem;
}

.error-banner {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 14px;
    padding: 2rem;
    text-align: center;
    max-width: 600px;
    margin: 3rem auto;
}

.error-title {
    color: #f87171;
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.error-msg {
    color: #d1d5db;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}

.empty-state {
    text-align: center;
    padding: 4rem 1.5rem;
    color: #9ca3af;
}

.empty-state h3 {
    color: #ffffff;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

/* -------------------------------------------------------------
   Netflix-Style Recommendation Rows
   ------------------------------------------------------------- */
.row-section {
    margin-bottom: 2.75rem;
    position: relative;
}

.row-title {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #f3f4f6;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.row-scroll-container {
    display: flex;
    gap: 1.25rem;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    padding: 0.75rem 0.5rem 1.25rem 0.5rem;
    /* Hide scrollbars */
    scrollbar-width: none;
    -ms-overflow-style: none;
    /* Edge fade */
    mask-image: linear-gradient(to right, transparent, black 16px, black calc(100% - 16px), transparent);
    -webkit-mask-image: linear-gradient(to right, transparent, black 16px, black calc(100% - 16px), transparent);
}

.row-scroll-container::-webkit-scrollbar {
    display: none;
}

/* -------------------------------------------------------------
   Repo Card
   ------------------------------------------------------------- */
.repo-card {
    min-width: 320px;
    max-width: 320px;
    flex: 0 0 320px;
    background-color: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    padding: 1.25rem;
    scroll-snap-align: start;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                border-color 0.25s ease;
}

.repo-card:hover {
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(124, 58, 237, 0.55);
    box-shadow: 0 10px 28px rgba(124, 58, 237, 0.3);
    z-index: 2;
}

.card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.85rem;
}

.lang-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #9ca3af;
}

.owner-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}

.owner-img {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    object-fit: cover;
}

.owner-fallback {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background-color: #374151;
    color: #ffffff;
    font-size: 0.7rem;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
}

.card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.45rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card-desc {
    font-size: 0.85rem;
    color: #9ca3af;
    line-height: 1.45;
    margin-bottom: 1.25rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 2.5rem;
}

.card-bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.star-count {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #e5e7eb;
}

.star-icon {
    color: #eab308;
}

.gh-button {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: #ffffff;
    background-color: #7c3aed;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    text-decoration: none !important;
    opacity: 0;
    transform: translateY(2px);
    transition: opacity 0.2s ease, transform 0.2s ease, background-color 0.2s ease;
}

.repo-card:hover .gh-button {
    opacity: 1;
    transform: translateY(0);
}

.gh-button:hover {
    background-color: #6d28d9;
}

/* -------------------------------------------------------------
   Skeleton Loading State
   ------------------------------------------------------------- */
@keyframes pulse {
    0%, 100% { opacity: 0.35; }
    50% { opacity: 0.75; }
}

.skeleton-row {
    margin-bottom: 2.5rem;
}

.skeleton-title {
    width: 220px;
    height: 24px;
    background-color: #1f2937;
    border-radius: 6px;
    margin-bottom: 1rem;
    animation: pulse 1.8s ease-in-out infinite;
}

.skeleton-grid {
    display: flex;
    gap: 1.25rem;
    overflow: hidden;
}

.skeleton-card {
    min-width: 320px;
    height: 180px;
    background-color: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 14px;
    padding: 1.25rem;
    animation: pulse 1.8s ease-in-out infinite;
}

/* -------------------------------------------------------------
   Footer
   ------------------------------------------------------------- */
.gitflix-footer {
    text-align: center;
    padding: 3rem 0 2rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    margin-top: 4rem;
    color: #6b7280;
    font-size: 0.85rem;
    line-height: 1.6;
}

.gitflix-footer span {
    color: #9ca3af;
}
</style>
"""
