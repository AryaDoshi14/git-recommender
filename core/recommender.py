"""Recommendation engine for GitFlix.

Generates Netflix-style categorized rows of repositories using GitHub search,
vector embeddings, cosine similarity, and multi-tier fallbacks.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from core.config import COLD_START_THRESHOLD
from core.embeddings import cosine_similarity, get_batch_embeddings, is_valid_embedding
from core.github_client import search_repos


# Non-programming markup/style formats that often inflate repository byte counts
MARKUP_LANGUAGES = {"html", "css", "scss", "sass", "less", "tex", "markdown"}


def _get_dates() -> Tuple[str, str]:
    """Return dates formatted as YYYY-MM-DD for 6 months ago and 7 days ago."""
    now = datetime.now(timezone.utc)
    six_months = (now - timedelta(days=180)).strftime("%Y-%m-%d")
    seven_days = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    return six_months, seven_days


def get_stack_languages(
    top_languages: Dict[str, float],
    stars: List[Dict[str, Any]],
    max_langs: int = 4,
) -> List[str]:
    """Extract languages in true stack order (most prominent first), supplemented by stars."""
    ordered: List[str] = []
    # 1. Top languages in descending order of presence
    for lang in top_languages.keys():
        if lang and lang not in ordered:
            ordered.append(lang)

    # 2. Add languages from starred repos
    for star in stars:
        slang = star.get("language")
        if slang and slang not in ordered:
            ordered.append(slang)
        if len(ordered) >= max_langs:
            break

    if not ordered:
        return ["TypeScript"]

    return ordered[:max_langs]


def interleave_repos(repo_lists: List[List[Dict[str, Any]]], limit: int = 10) -> List[Dict[str, Any]]:
    """Interleave repositories from multiple language lists in round-robin fashion.

    Ensures balanced, moderate representation of all languages in a stack without duplicates.
    """
    result: List[Dict[str, Any]] = []
    seen_ids = set()
    max_len = max((len(lst) for lst in repo_lists), default=0)

    for i in range(max_len):
        for lst in repo_lists:
            if i < len(lst):
                repo = lst[i]
                repo_id = repo.get("id")
                if repo_id is not None:
                    if repo_id not in seen_ids:
                        seen_ids.add(repo_id)
                        result.append(repo)
                else:
                    result.append(repo)
                if len(result) >= limit:
                    return result

    return result


def deduplicate_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate repositories across all rows by repo id (first occurrence wins).

    Drops rows that become empty after deduplication.
    """
    seen_ids = set()
    cleaned_rows: List[Dict[str, Any]] = []

    for row in rows:
        title = row.get("title", "")
        repos = row.get("repos", [])
        unique_repos = []
        for repo in repos:
            repo_id = repo.get("id")
            if repo_id is not None:
                if repo_id not in seen_ids:
                    seen_ids.add(repo_id)
                    unique_repos.append(repo)
            else:
                unique_repos.append(repo)

        if unique_repos:
            cleaned_rows.append({"title": title, "repos": unique_repos})

    return cleaned_rows


def compute_profile_vector(
    stars: List[Dict[str, Any]],
    star_embeddings: Dict[str, List[float]],
) -> Optional[List[float]]:
    """Compute weighted profile vector from starred repos.

    First 20 stars get weight 2, subsequent stars get weight 1.
    """
    weighted_vectors: List[np.ndarray] = []
    total_weights = 0.0

    for idx, repo in enumerate(stars):
        fname = repo.get("full_name") or f"{repo.get('owner', {}).get('login', '')}/{repo.get('name', '')}"
        vec = star_embeddings.get(fname)
        if is_valid_embedding(vec):
            weight = 2.0 if idx < 20 else 1.0
            weighted_vectors.append(np.asarray(vec, dtype=np.float64) * weight)
            total_weights += weight

    if not weighted_vectors or total_weights == 0.0:
        return None

    summed = np.sum(weighted_vectors, axis=0)
    profile_vector = (summed / total_weights).tolist()
    return profile_vector if is_valid_embedding(profile_vector) else None


def get_recommendations(
    stars: List[Dict[str, Any]],
    owned: List[Dict[str, Any]],
    top_languages: Dict[str, float],
) -> Tuple[List[Dict[str, Any]], bool]:
    """Generate categorized Netflix-style repository recommendation rows.

    Distributes recommendations across all languages in the user's stack moderately,
    preserving the most prominent language while giving balanced representation.

    Args:
        stars: User's starred repositories.
        owned: User's owned repositories.
        top_languages: Dict of languages to percentage shares.

    Returns:
        Tuple of (rows, is_cold_start), where each row is {"title": str, "repos": list}.
    """
    stack_langs = get_stack_languages(top_languages, stars)
    primary_lang = stack_langs[0]

    six_months_ago, seven_days_ago = _get_dates()

    # 1. COLD START (fewer than 5 stars)
    if len(stars) < COLD_START_THRESHOLD:
        with ThreadPoolExecutor(max_workers=6) as executor:
            pop_futures = [
                executor.submit(search_repos, f"language:{l} stars:>1000", sort="stars", per_page=6)
                for l in stack_langs
            ]
            gem_futures = {
                l: executor.submit(search_repos, f"language:{l} stars:50..500", sort="updated", per_page=10)
                for l in stack_langs
            }

            pop_lists = [f.result() for f in pop_futures if f.result()]
            balanced_pop = interleave_repos(pop_lists, limit=10)

            raw_rows = [
                {"title": "Popular in your stack", "repos": balanced_pop},
            ]
            for l, fut in gem_futures.items():
                res = fut.result()
                if res:
                    raw_rows.append({"title": f"Underrated Gems in {l}", "repos": res})

        filtered = [r for r in raw_rows if r.get("repos")]
        return deduplicate_rows(filtered), True

    # 2. Regular Personalized Flow
    star_embeddings = get_batch_embeddings(stars)
    profile_vec = compute_profile_vector(stars, star_embeddings)

    anchor_repo = stars[0]
    anchor_fname = anchor_repo.get("full_name") or f"{anchor_repo.get('owner', {}).get('login', '')}/{anchor_repo.get('name', '')}"
    anchor_embedding = star_embeddings.get(anchor_fname)

    def _build_row_a() -> Optional[Dict[str, Any]]:
        if not is_valid_embedding(anchor_embedding):
            return None
        anchor_lang = anchor_repo.get("language") or primary_lang
        candidates = search_repos(
            f"language:{anchor_lang} stars:>1000",
            sort="stars",
            per_page=30,
        )
        if not candidates:
            return None

        # Exclude anchor itself
        filtered = [
            c for c in candidates
            if c.get("id") != anchor_repo.get("id") and c.get("full_name") != anchor_fname
        ]
        if not filtered:
            return None

        cand_embeddings = get_batch_embeddings(filtered)
        scored = []
        for c in filtered:
            cfname = c.get("full_name") or f"{c.get('owner', {}).get('login', '')}/{c.get('name', '')}"
            vec = cand_embeddings.get(cfname)
            sim = cosine_similarity(vec, anchor_embedding) if vec else 0.0
            scored.append((sim, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top10 = [c for _, c in scored[:10]]
        return {"title": f"Because you starred {anchor_repo.get('name', 'this repo')}", "repos": top10}

    def _build_row_b() -> Optional[Dict[str, Any]]:
        # "Trending in your stack" - balanced moderately across all user languages
        repo_lists = []
        for l in stack_langs:
            res = search_repos(f"language:{l} stars:>500", sort="updated", per_page=6)
            if res:
                repo_lists.append(res)
        balanced = interleave_repos(repo_lists, limit=10)
        return {"title": "Trending in your stack", "repos": balanced} if balanced else None

    def _build_row_c() -> Optional[Dict[str, Any]]:
        if not is_valid_embedding(profile_vec):
            return None
        candidates = search_repos(
            f"stars:50..500 pushed:>{six_months_ago}",
            sort="updated",
            per_page=50,
        )
        if not candidates:
            return None

        cand_embeddings = get_batch_embeddings(candidates)
        scored = []
        for c in candidates:
            stargazers = c.get("stargazers_count", 0)
            if stargazers >= 2000:
                continue
            cfname = c.get("full_name") or f"{c.get('owner', {}).get('login', '')}/{c.get('name', '')}"
            vec = cand_embeddings.get(cfname)
            sim = cosine_similarity(vec, profile_vec) if vec else 0.0
            if sim > 0.45:
                scored.append((sim, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top10 = [c for _, c in scored[:10]]
        return {"title": "Hidden Gems", "repos": top10} if top10 else None

    def _build_row_d() -> Optional[Dict[str, Any]]:
        if not is_valid_embedding(profile_vec):
            return None
        candidates = search_repos(
            f"created:>{six_months_ago} stars:>100",
            sort="stars",
            per_page=50,
        )
        if not candidates:
            return None

        cand_embeddings = get_batch_embeddings(candidates)
        scored = []
        for c in candidates:
            cfname = c.get("full_name") or f"{c.get('owner', {}).get('login', '')}/{c.get('name', '')}"
            vec = cand_embeddings.get(cfname)
            sim = cosine_similarity(vec, profile_vec) if vec else 0.0
            if sim > 0.45:
                scored.append((sim, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top10 = [c for _, c in scored[:10]]
        return {"title": "New & Noteworthy", "repos": top10} if top10 else None

    def _build_row_e() -> Optional[Dict[str, Any]]:
        # "Popular in your stack" - balanced moderately across all user languages
        repo_lists = []
        for l in stack_langs:
            res = search_repos(f"language:{l} stars:>1000", sort="stars", per_page=6)
            if res:
                repo_lists.append(res)
        balanced = interleave_repos(repo_lists, limit=10)
        return {"title": "Popular in your stack", "repos": balanced} if balanced else None

    def _build_row_f() -> Optional[Dict[str, Any]]:
        # Underrated gems in primary (most prominent) language
        repos = search_repos(f"language:{primary_lang} stars:50..500", sort="updated", per_page=10)
        return {"title": f"Underrated Gems in {primary_lang}", "repos": repos} if repos else None

    def _build_row_g() -> Optional[Dict[str, Any]]:
        # Underrated gems in secondary language if user has more than 1 language
        if len(stack_langs) > 1:
            second_lang = stack_langs[1]
            repos = search_repos(f"language:{second_lang} stars:50..500", sort="updated", per_page=10)
            return {"title": f"Underrated Gems in {second_lang}", "repos": repos} if repos else None
        return None

    # Fetch rows concurrently
    with ThreadPoolExecutor(max_workers=7) as executor:
        futs = {
            "A": executor.submit(_build_row_a),
            "B": executor.submit(_build_row_b),
            "C": executor.submit(_build_row_c),
            "D": executor.submit(_build_row_d),
            "E": executor.submit(_build_row_e),
            "F": executor.submit(_build_row_f),
            "G": executor.submit(_build_row_g),
        }

        row_results: Dict[str, Optional[Dict[str, Any]]] = {
            key: fut.result() for key, fut in futs.items()
        }

    # Order rows: A, B, E, C, D, F, G
    ordered_keys = ["A", "B", "E", "C", "D", "F", "G"]
    collected_rows: List[Dict[str, Any]] = []
    for k in ordered_keys:
        item = row_results.get(k)
        if item and item.get("repos"):
            collected_rows.append(item)

    # If fewer than 3 rows remain, append "Trending this week"
    if len(collected_rows) < 3:
        fallback_repos = search_repos(
            f"stars:>5000 pushed:>{seven_days_ago}",
            sort="updated",
            per_page=10,
        )
        if fallback_repos:
            collected_rows.append({"title": "Trending this week", "repos": fallback_repos})

    # Deduplicate repos across ALL rows by repo id (first occurrence wins)
    final_rows = deduplicate_rows(collected_rows)
    return final_rows, False
