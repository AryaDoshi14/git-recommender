"""Tests for core/orchestrator.py."""

import pytest
from unittest.mock import patch

from core.errors import GitHubError
from core.orchestrator import load_profile
from core import cache


def test_load_profile_empty_username_raises_error():
    """Verify empty or whitespace username raises GitHubError with status 400."""
    with pytest.raises(GitHubError) as exc:
        load_profile("   ")
    assert exc.value.status == 400
    assert "cannot be empty" in exc.value.message


def test_load_profile_returns_cached_result(monkeypatch):
    """Verify cached profile recommendations are returned directly without calling GitHub."""
    cached_payload = {
        "user": {"login": "cacheduser"},
        "languages": {"Python": 100.0},
        "rows": [{"title": "Cached Row", "repos": []}],
        "cold_start": False,
    }
    cache.set("recommendations:cacheduser", cached_payload, ttl=60)

    # Calling load_profile should return the cached payload without needing any network mocks
    res = load_profile("cacheduser")
    assert res == cached_payload
    assert res["user"]["login"] == "cacheduser"


def test_load_profile_full_flow():
    """Verify complete orchestration flow with mocked underlying functions."""
    mock_user = {"login": "newuser", "name": "New User"}
    mock_starred = [{"id": 1, "name": "s1", "full_name": "newuser/s1"}]
    mock_owned = [{"id": 2, "name": "o1", "full_name": "newuser/o1"}]

    with patch("core.orchestrator.fetch_user_profile", return_value=mock_user), \
         patch("core.orchestrator.fetch_starred_repos", return_value=mock_starred), \
         patch("core.orchestrator.fetch_owned_repos", return_value=mock_owned), \
         patch("core.orchestrator.calculate_language_weights", return_value={"Python": 100.0}), \
         patch("core.orchestrator.get_recommendations", return_value=([{"title": "Test Row", "repos": []}], True)):

        result = load_profile("newuser")
        assert result["user"]["login"] == "newuser"
        assert result["cold_start"] is True
        assert len(result["rows"]) == 1
