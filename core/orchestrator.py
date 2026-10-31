"""Orchestrates profile loading, concurrent data aggregation, and recommendation pipeline.
"""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict

from core import cache
from core.config import COLD_START_TTL, RESULT_TTL
from core.errors import GitHubError
from core.github_client import fetch_owned_repos, fetch_starred_repos, fetch_user_profile
from core.languages import calculate_language_weights
from core.recommender import get_recommendations


def _load_profile_internal(username: str) -> Dict[str, Any]:
    """Execute pipeline: fetch profile, repos, compute language stats, and generate recommendations."""
    # Fetch profile, starred, and owned in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        fut_profile = executor.submit(fetch_user_profile, username)
        fut_starred = executor.submit(fetch_starred_repos, username)
        fut_owned = executor.submit(fetch_owned_repos, username)

        profile = fut_profile.result()
        starred = fut_starred.result()
        owned = fut_owned.result()

    # Calculate language weights from owned repositories; fallback to starred if owned has none
    languages = calculate_language_weights(owned)
    if not languages and starred:
        languages = calculate_language_weights(starred)

    # Generate recommendations
    rows, cold_start = get_recommendations(starred, owned, languages)

    return {
        "user": profile,
        "languages": languages,
        "rows": rows,
        "cold_start": cold_start,
    }


def load_profile(username: str, timeout_seconds: int = 25) -> Dict[str, Any]:
    """Load profile, languages, and recommendations for a given GitHub username.

    Validates input, checks cache, aggregates GitHub profile & repository data concurrently,
    and caches final result with either COLD_START_TTL or RESULT_TTL.

    Args:
        username: GitHub username.
        timeout_seconds: Overall ceiling timeout in seconds (default 25s).

    Raises:
        GitHubError: If username is empty, API errors occur, or overall timeout expires.
    """
    clean_username = username.strip() if username else ""
    if not clean_username:
        raise GitHubError("Username cannot be empty.", status=400)

    cache_key = f"recommendations:{clean_username.lower()}"
    cached_result = cache.get(cache_key)
    if cached_result and isinstance(cached_result, dict):
        return cached_result

    # Run internal workflow with a 25-second ceiling
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_load_profile_internal, clean_username)
        try:
            result = future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise GitHubError(
                "Request timed out, heavy profiles may need a second attempt.",
                status=408,
            )

    # Cache result based on cold_start status
    ttl = COLD_START_TTL if result.get("cold_start") else RESULT_TTL
    cache.set(cache_key, result, ttl=ttl)

    return result
