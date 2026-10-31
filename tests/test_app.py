"""Streamlit AppTest smoke tests for app.py."""

from streamlit.testing.v1 import AppTest


def test_app_welcome_page_smoke():
    """Verify that the initial application load renders the welcome state without errors."""
    at = AppTest.from_file("../app.py", default_timeout=15)
    at.run()

    # Ensure no unhandled exceptions were raised
    assert not at.exception

    # Check markdown contents for the Welcome to GitFlix elements and logo
    combined_markdown = " ".join([m.value for m in at.markdown])
    assert "Welcome to GitFlix" in combined_markdown
    assert "GITFLIX" in combined_markdown
    assert "Vector Matching" in combined_markdown
