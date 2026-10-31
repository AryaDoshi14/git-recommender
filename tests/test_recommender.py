"""Tests for core/recommender.py and core/languages.py."""

from unittest.mock import patch
from core.languages import calculate_language_weights
from core.recommender import (
    compute_profile_vector,
    deduplicate_rows,
    get_recommendations,
)


def test_calculate_language_weights_math_and_sorting(monkeypatch):
    """Test language byte percentage calculation, descending sorting, and rounding."""
    # Mock fetch_languages_for_repo
    sample_lang_data = {
        ("alice", "repo1"): {"Python": 7000, "TypeScript": 3000},
        ("alice", "repo2"): {"Python": 1000, "Go": 2000},
    }

    def mock_fetch(owner, repo):
        return sample_lang_data.get((owner, repo), {})

    monkeypatch.setattr("core.languages.fetch_languages_for_repo", mock_fetch)

    repos = [
        {"full_name": "alice/repo1", "owner": {"login": "alice"}, "name": "repo1"},
        {"full_name": "alice/repo2", "owner": {"login": "alice"}, "name": "repo2"},
    ]

    # Total bytes = 7000 + 3000 + 1000 + 2000 = 13,000
    # Python = 8000 / 13000 = 61.538% -> 61.54%
    # TypeScript = 3000 / 13000 = 23.076% -> 23.08%
    # Go = 2000 / 13000 = 15.384% -> 15.38%
    weights = calculate_language_weights(repos)
    assert list(weights.keys()) == ["Python", "TypeScript", "Go"]
    assert weights["Python"] == 61.54
    assert weights["TypeScript"] == 23.08
    assert weights["Go"] == 15.38


def test_calculate_language_weights_zero_bytes(monkeypatch):
    """Test calculate_language_weights returns {} if total bytes is 0."""
    monkeypatch.setattr("core.languages.fetch_languages_for_repo", lambda o, r: {})
    repos = [{"full_name": "alice/empty", "owner": {"login": "alice"}, "name": "empty"}]
    assert calculate_language_weights(repos) == {}


def test_deduplicate_rows_cross_row_and_drop_empty():
    """Test deduplicate_rows keeps first occurrence by repo id and removes empty rows."""
    repo_a = {"id": 101, "name": "RepoA"}
    repo_b = {"id": 102, "name": "RepoB"}
    repo_c = {"id": 103, "name": "RepoC"}

    rows = [
        {"title": "Row 1", "repos": [repo_a, repo_b]},
        {"title": "Row 2", "repos": [repo_b, repo_c]},  # repo_b is duplicate, repo_c is kept
        {"title": "Row 3", "repos": [repo_a, repo_b]},  # all duplicates -> row dropped
    ]

    deduped = deduplicate_rows(rows)
    assert len(deduped) == 2
    assert deduped[0]["title"] == "Row 1"
    assert [r["id"] for r in deduped[0]["repos"]] == [101, 102]

    assert deduped[1]["title"] == "Row 2"
    assert [r["id"] for r in deduped[1]["repos"]] == [103]


def test_cold_start_threshold_4_stars():
    """Test 4 stars triggers cold start."""
    stars_4 = [{"id": i, "name": f"star-{i}", "full_name": f"user/star-{i}"} for i in range(4)]
    mock_search_results = [{"id": 999, "name": "popular-repo"}]

    with patch("core.recommender.search_repos", return_value=mock_search_results):
        rows, is_cold_start = get_recommendations(stars_4, [], {"Python": 100.0})

    assert is_cold_start is True
    assert len(rows) > 0
    assert rows[0]["title"] == "Popular in your stack"


def test_cold_start_threshold_5_stars():
    """Test 5 stars is NOT cold start and builds full recommendation profile."""
    stars_5 = [
        {"id": i, "name": f"star-{i}", "full_name": f"user/star-{i}", "language": "Python"}
        for i in range(5)
    ]
    # Mock embeddings
    mock_embeddings = {f"user/star-{i}": [0.1, 0.2, 0.3] for i in range(5)}
    mock_search = [{"id": 200 + i, "name": f"cand-{i}", "full_name": f"user/cand-{i}"} for i in range(5)]

    with patch("core.recommender.get_batch_embeddings", return_value=mock_embeddings), \
         patch("core.recommender.search_repos", return_value=mock_search):
        rows, is_cold_start = get_recommendations(stars_5, [], {"Python": 100.0})

    assert is_cold_start is False
    assert len(rows) > 0


def test_compute_profile_vector_weights():
    """Test first 20 stars get weight 2, subsequent stars get weight 1."""
    stars = [{"full_name": f"u/repo-{i}"} for i in range(25)]
    # First 20 are [1.0], rest 5 are [0.0]
    # Total weight: 20 * 2.0 = 40; 5 * 1.0 = 5. Total = 45.
    # Sum: 40 * 1.0 + 5 * 0.0 = 40.0. Average: 40 / 45 = 0.8888...
    embeddings = {}
    for i in range(20):
        embeddings[f"u/repo-{i}"] = [1.0]
    for i in range(20, 25):
        embeddings[f"u/repo-{i}"] = [0.0]

    vec = compute_profile_vector(stars, embeddings)
    assert vec is not None
    assert round(vec[0], 4) == round(40.0 / 45.0, 4)


def test_get_stack_languages():
    """Verify stack languages preserve true prominent order and include starred languages."""
    from core.recommender import get_stack_languages

    # HTML 70%, Python 20%, JavaScript 10%
    top_langs = {"HTML": 70.0, "Python": 20.0, "JavaScript": 10.0}
    stars = [{"language": "Go"}]

    res = get_stack_languages(top_langs, stars)
    # Most prominent language stays first!
    assert res[0] == "HTML"
    assert res[1] == "Python"
    assert res[2] == "JavaScript"
    assert "Go" in res


def test_interleave_repos():
    """Verify interleave_repos balances repositories across multiple language lists."""
    from core.recommender import interleave_repos

    list1 = [{"id": 1, "name": "html-1"}, {"id": 2, "name": "html-2"}]
    list2 = [{"id": 3, "name": "py-1"}, {"id": 4, "name": "py-2"}]
    list3 = [{"id": 5, "name": "js-1"}, {"id": 6, "name": "js-2"}]

    interleaved = interleave_repos([list1, list2, list3], limit=6)
    # Verify round-robin alternating order
    assert [r["id"] for r in interleaved] == [1, 3, 5, 2, 4, 6]


def test_multi_language_cold_start_rows():
    """Verify cold start with multiple languages generates rows for multiple languages."""
    stars = [{"id": 1, "name": "s1"}]

    def _mock_search(query, **kwargs):
        # Return unique repo per query to avoid cross-row deduplication drop
        return [{"id": abs(hash(query)), "name": f"repo-for-{query[:15]}"}]

    with patch("core.recommender.search_repos", side_effect=_mock_search):
        rows, is_cold_start = get_recommendations(
            stars,
            [],
            {"HTML": 60.0, "Python": 40.0},
        )

    assert is_cold_start is True
    titles = [r["title"] for r in rows]
    # At least one row for stack / Python, and should include rows for other languages
    assert any("Python" in t or "stack" in t for t in titles)
    assert any("HTML" in t for t in titles)

