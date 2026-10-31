"""Language statistics and weight calculations for GitHub repositories.

Analyzes language byte distributions across owned repositories, leveraging cache and parallel fetches.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from core import cache
from core.config import LONG_TTL, MAX_LANG_REPOS
from core.github_client import fetch_languages_for_repo


def calculate_language_weights(repos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate the percentage distribution of programming languages across repositories.

    Args:
        repos: List of GitHub repository metadata dictionaries.

    Returns:
        Dict mapping language name to its percentage share (e.g., {'Python': 65.4, 'Rust': 34.6}),
        sorted descending by percentage. Returns {} if no bytes are found or repos list is empty.
    """
    if not repos:
        return {}

    target_repos = repos[:MAX_LANG_REPOS]

    # Map full_name to repo dictionary for repos that have owner and name
    valid_repos: List[Dict[str, Any]] = []
    cache_keys: List[str] = []
    for r in target_repos:
        full_name = r.get("full_name") or f"{r.get('owner', {}).get('login')}/{r.get('name')}"
        if full_name and "/" in full_name:
            valid_repos.append(r)
            cache_keys.append(f"lang:{full_name}")

    if not valid_repos:
        return {}

    # Bulk-check cache
    cached_hits = cache.mget(cache_keys)
    misses: List[Dict[str, Any]] = []
    repo_lang_data: List[Dict[str, int]] = []

    for r, key in zip(valid_repos, cache_keys):
        if key in cached_hits and isinstance(cached_hits[key], dict):
            repo_lang_data.append(cached_hits[key])
        else:
            misses.append(r)

    # Fetch misses in parallel
    if misses:
        newly_fetched: Dict[str, Dict[str, int]] = {}

        def _fetch_one(repo: Dict[str, Any]) -> tuple[str, Dict[str, int]]:
            full_name = repo.get("full_name") or f"{repo.get('owner', {}).get('login')}/{repo.get('name')}"
            try:
                owner, name = full_name.split("/", 1)
                data = fetch_languages_for_repo(owner, name)
                return full_name, data if isinstance(data, dict) else {}
            except Exception:
                # Swallow per-repo failure and treat as empty dict
                return full_name, {}

        with ThreadPoolExecutor(max_workers=min(10, len(misses))) as executor:
            future_to_repo = {executor.submit(_fetch_one, repo): repo for repo in misses}
            for future in as_completed(future_to_repo):
                try:
                    full_name, lang_dict = future.result()
                    newly_fetched[f"lang:{full_name}"] = lang_dict
                    repo_lang_data.append(lang_dict)
                except Exception:
                    repo_lang_data.append({})

        # Cache fetched results for 7 days
        if newly_fetched:
            cache.mset(newly_fetched, ttl=LONG_TTL)

    # Sum bytes per language
    totals: Dict[str, int] = {}
    for lang_dict in repo_lang_data:
        for lang, byte_count in lang_dict.items():
            if isinstance(byte_count, (int, float)) and byte_count > 0:
                totals[lang] = totals.get(lang, 0) + int(byte_count)

    total_bytes = sum(totals.values())
    if total_bytes == 0:
        return {}

    # Convert to percentages rounded to 2 decimals, sorted descending
    percentages = {
        lang: round((count / total_bytes) * 100, 2)
        for lang, count in totals.items()
    }

    # Sort descending by percentage
    return dict(sorted(percentages.items(), key=lambda item: item[1], reverse=True))
