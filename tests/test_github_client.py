"""Tests for core/github_client.py and core/errors.py."""

import pytest
import responses

from core.errors import GitHubError
from core.github_client import (
    fetch_starred_repos,
    fetch_user_profile,
    get_headers,
    handle_api_error,
    search_repos,
)
from core import config


def test_get_headers_with_and_without_token(monkeypatch):
    """Test get_headers properly attaches Bearer token only when GITHUB_TOKEN is set."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    headers = get_headers()
    assert "Authorization" not in headers
    assert headers["Accept"] == "application/vnd.github.v3+json"

    monkeypatch.setattr(config, "GITHUB_TOKEN", "ghp_test123")
    headers_with_token = get_headers()
    assert headers_with_token["Authorization"] == "Bearer ghp_test123"


def test_handle_api_error_404():
    """Test 404 response maps to 'GitHub User Not Found.'"""
    resp = responses.Response(
        method="GET",
        url="https://api.github.com/users/nonexistentuser",
        status=404,
        json={"message": "Not Found"},
    )
    # Convert mock to actual response using requests session
    import requests
    with responses.RequestsMock() as rsps:
        rsps.add(resp)
        r = requests.get("https://api.github.com/users/nonexistentuser")
        with pytest.raises(GitHubError) as exc_info:
            handle_api_error(r)
        assert exc_info.value.status == 404
        assert exc_info.value.message == "GitHub User Not Found."


def test_handle_api_error_rate_limits():
    """Test 403 with X-RateLimit-Remaining 0 and 429 secondary rate limit."""
    import requests
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://api.github.com/rate403",
            status=403,
            headers={"X-RateLimit-Remaining": "0"},
        )
        r403 = requests.get("https://api.github.com/rate403")
        with pytest.raises(GitHubError) as exc403:
            handle_api_error(r403)
        assert "Rate Limit Exceeded" in exc403.value.message
        assert exc403.value.status == 403

        rsps.add(
            responses.GET,
            "https://api.github.com/rate429",
            status=429,
            headers={"Retry-After": "60"},
        )
        r429 = requests.get("https://api.github.com/rate429")
        with pytest.raises(GitHubError) as exc429:
            handle_api_error(r429)
        assert "Secondary Rate Limit" in exc429.value.message
        assert exc429.value.retry_after == 60


@responses.activate
def test_fetch_starred_repos_partial_results_on_page_2_rate_limit():
    """Test that if page 1 succeeds and page 2 hits a 403/429, partial results are returned."""
    # Page 1 returns 100 items
    page_1_data = [{"id": i, "name": f"repo-{i}"} for i in range(100)]
    responses.add(
        responses.GET,
        "https://api.github.com/users/testuser/starred?page=1&per_page=100",
        json=page_1_data,
        status=200,
    )
    # Page 2 hits 403 rate limit
    responses.add(
        responses.GET,
        "https://api.github.com/users/testuser/starred?page=2&per_page=100",
        status=403,
        headers={"X-RateLimit-Remaining": "0"},
    )

    starred = fetch_starred_repos("testuser")
    assert len(starred) == 100
    assert starred[0]["name"] == "repo-0"
    assert starred[99]["name"] == "repo-99"


@responses.activate
def test_fetch_user_profile_404_raises_error():
    """Test fetch_user_profile raises hard GitHubError on 404."""
    responses.add(
        responses.GET,
        "https://api.github.com/users/unknown_dev_12345",
        status=404,
        json={"message": "Not Found"},
    )
    with pytest.raises(GitHubError) as exc:
        fetch_user_profile("unknown_dev_12345")
    assert exc.value.status == 404
    assert exc.value.message == "GitHub User Not Found."


@responses.activate
def test_search_repos_returns_empty_on_error():
    """Test search_repos swallows exceptions and returns empty list."""
    responses.add(
        responses.GET,
        "https://api.github.com/search/repositories?q=test&per_page=10",
        status=500,
    )
    res = search_repos("test")
    assert res == []
