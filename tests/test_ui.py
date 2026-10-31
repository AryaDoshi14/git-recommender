"""Tests for ui/colors.py and ui/components.py."""

from ui.colors import LANGUAGE_COLORS, get_language_color
from ui.components import format_stars, render_repo_card, render_skeleton


def test_language_colors_lookup():
    """Verify official language colors and case-insensitive default lookups."""
    # Exact match
    assert get_language_color("Python") == "#3776ab"
    assert get_language_color("TypeScript") == "#3178c6"
    assert get_language_color("Rust") == "#dea584"

    # Case-insensitive
    assert get_language_color("python") == "#3776ab"
    assert get_language_color("TYPESCRIPT") == "#3178c6"

    # Unknown language defaults to #808080
    assert get_language_color("Brainfuck") == "#808080"
    assert get_language_color(None) == "#808080"
    assert get_language_color("") == "#808080"

    # Check total colors count
    assert len(LANGUAGE_COLORS) >= 20


def test_format_stars():
    """Verify star formatting for small and large counts."""
    assert format_stars(0) == "0"
    assert format_stars(450) == "450"
    assert format_stars(999) == "999"
    assert format_stars(1000) == "1k"
    assert format_stars(1200) == "1.2k"
    assert format_stars(15400) == "15.4k"


def test_render_repo_card_escapes_html():
    """Verify repo card escapes malicious input and includes secure external link tags."""
    xss_repo = {
        "id": 1,
        "name": "<script>alert('xss')</script>",
        "description": "<img src=x onerror=alert(1)>",
        "language": "Python",
        "stargazers_count": 1250,
        "html_url": "https://github.com/evil/repo",
        "owner": {"login": "attacker<evil>", "avatar_url": "https://example.com/avatar.png"},
    }

    card_html = render_repo_card(xss_repo)
    # Check that script and img tags were escaped
    assert "<script>" not in card_html
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in card_html
    assert "<img src=x onerror=alert(1)>" not in card_html
    assert "&lt;img src=x onerror=alert(1)&gt;" in card_html
    assert 'target="_blank"' in card_html
    assert 'rel="noopener noreferrer"' in card_html


def test_render_skeleton():
    """Verify skeleton HTML structure."""
    skeleton_html = render_skeleton()
    assert "skeleton-card" in skeleton_html
    assert "skeleton-row" in skeleton_html
