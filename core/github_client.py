"""GitHub REST API v3 client for GitFlix.

Handles authentication, pagination, rate limits, search query formatting, and error mapping.
"""

import re
from typing import Any, Dict, List, Optional
import requests

from core import config
from core.config import (
    GITHUB_API_URL,
    MAX_STARRED_PAGES,
    PER_PAGE,
)
from core.errors import GitHubError


def get_headers() -> Dict[str, str]:
    """Build request headers for GitHub API.

    Accepts v3 JSON, and attaches Bearer authorization only if GITHUB_TOKEN is set.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitFlix-Recommender",
    }
    token = config.GITHUB_TOKEN
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def handle_api_error(response: requests.Response) -> None:
    """Evaluate response status and headers, raising appropriate GitHubError."""
    status = response.status_code
    retry_after: Optional[int] = None
    retry_header = response.headers.get("Retry-After")
    if retry_header:
        try:
            retry_after = int(retry_header)
        except ValueError:
            retry_after = None

    remaining = response.headers.get("X-RateLimit-Remaining")

    if status == 403 and remaining == "0":
        msg = "GitHub Rate Limit Exceeded."
    elif status == 429 or "Retry-After" in response.headers:
        msg = "Secondary Rate Limit Hit."
    elif status == 404:
        msg = "GitHub User Not Found."
    else:
        msg = f"GitHub API Error: {status}"

    raise GitHubError(message=msg, status=status, retry_after=retry_after)


def quote_language_in_query(query: str) -> str:
    """Ensure languages with spaces in search query are quoted (e.g., language:"Jupyter Notebook")."""
    def _repl(match: re.Match) -> str:
        lang = match.group(1).strip('"')
        if " " in lang:
            return f'language:"{lang}"'
        return match.group(0)

    return re.sub(r'language:([^\s]+)', _repl, query)


def github_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Perform a GET request to GitHub API using requests with timeout=20.

    Uses requests params= instead of manual query strings.
    """
    url = path if path.startswith("http") else f"{GITHUB_API_URL}/{path.lstrip('/')}"
    response = requests.get(url, headers=get_headers(), params=params, timeout=20)
    if not (200 <= response.status_code < 300):
        handle_api_error(response)
    return response.json()


def fetch_user_profile(username: str) -> Dict[str, Any]:
    """Fetch GitHub user profile. Raises GitHubError on any failure."""
    return github_get(f"/users/{username}")


def fetch_owned_repos(username: str) -> List[Dict[str, Any]]:
    """Fetch user's owned repositories (per_page=100, sorted by pushed desc, filtering forks)."""
    params = {
        "per_page": PER_PAGE,
        "sort": "pushed",
        "direction": "desc",
        "type": "owner",
    }
    data = github_get(f"/users/{username}/repos", params=params)
    if not isinstance(data, list):
        return []
    # Filter out forks as specified
    return [repo for repo in data if not repo.get("fork", False)]


def fetch_starred_repos(username: str) -> List[Dict[str, Any]]:
    """Fetch up to 3 pages of starred repos (max 300).

    On 403/429 mid-loop returns partial results.
    Stops when a page is short (< 100) or empty.
    """
    all_starred: List[Dict[str, Any]] = []

    for page in range(1, MAX_STARRED_PAGES + 1):
        params = {"page": page, "per_page": PER_PAGE}
        try:
            page_data = github_get(f"/users/{username}/starred", params=params)
        except GitHubError as err:
            # If mid-loop (we already collected some pages) and hit rate limit, return partial results
            if err.status in (403, 429) and len(all_starred) > 0:
                break
            raise

        if not isinstance(page_data, list) or len(page_data) == 0:
            break

        all_starred.extend(page_data)

        # Stop when page is short (< PER_PAGE)
        if len(page_data) < PER_PAGE:
            break

    return all_starred


def fetch_languages_for_repo(owner: str, repo: str) -> Dict[str, int]:
    """Fetch language byte breakdown for a specific repository."""
    data = github_get(f"/repos/{owner}/{repo}/languages")
    if isinstance(data, dict):
        return data
    return {}


def search_repos(query: str, sort: Optional[str] = None, per_page: int = 10) -> List[Dict[str, Any]]:
    """Search repositories matching query. Returns [] on any error."""
    clean_query = quote_language_in_query(query)
    params: Dict[str, Any] = {"q": clean_query, "per_page": per_page}
    if sort:
        params["sort"] = sort

    try:
        data = github_get("/search/repositories", params=params)
        if isinstance(data, dict):
            return data.get("items", [])
    except Exception:
        # Spec: search_repos returns [] on any error
        return []
    return []
