"""Embedding generation, caching, and vector similarity calculations using OpenAI SDK via OpenRouter.
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
from openai import OpenAI

from core import cache, config
from core.config import EMBEDDING_MODEL, LONG_TTL, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

# Lazy initialized client
_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """Lazy initialize the OpenAI client pointed to OpenRouter."""
    global _client
    if _client is not None:
        return _client

    import os
    api_key = os.getenv("OPENROUTER_API_KEY") or config.OPENROUTER_API_KEY
    if not api_key:
        return None

    _client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/GitFlix",
            "X-Title": "GitFlix",
        },
    )
    return _client


def is_valid_embedding(embedding: Any) -> bool:
    """Check if input is a valid non-empty list or array of numbers."""
    if embedding is None:
        return False
    if isinstance(embedding, np.ndarray):
        return embedding.size > 0 and np.issubdtype(embedding.dtype, np.number)
    if isinstance(embedding, (list, tuple)):
        return len(embedding) > 0 and all(isinstance(x, (int, float)) and not np.isnan(x) for x in embedding)
    return False


def cosine_similarity(vec1: Any, vec2: Any) -> float:
    """Calculate cosine similarity between two numeric vectors using numpy.

    Returns 0.0 on invalid input, dimension mismatch, or zero magnitude.
    """
    if not is_valid_embedding(vec1) or not is_valid_embedding(vec2):
        return 0.0

    a = np.asarray(vec1, dtype=np.float64)
    b = np.asarray(vec2, dtype=np.float64)

    if a.shape != b.shape or a.ndim != 1:
        return 0.0

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0 or np.isnan(norm_a) or np.isnan(norm_b):
        return 0.0

    dot = np.dot(a, b)
    similarity = float(dot / (norm_a * norm_b))
    return max(-1.0, min(1.0, similarity))


def get_batch_embeddings(repos: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Retrieve embeddings for a list of repositories, utilizing caching and 50-item batches.

    Args:
        repos: List of repo dicts containing name, full_name, description, language.

    Returns:
        Dict mapping repo full_name to embedding vector (list of floats).
    """
    if not repos:
        return {}

    # Gather cache keys for valid repositories
    repo_map: Dict[str, Dict[str, Any]] = {}
    cache_keys: List[str] = []

    for r in repos:
        full_name = r.get("full_name") or f"{r.get('owner', {}).get('login', '')}/{r.get('name', '')}"
        if full_name and "/" in full_name:
            repo_map[full_name] = r
            cache_keys.append(f"embedding:{full_name}")

    if not repo_map:
        return {}

    results: Dict[str, List[float]] = {}
    cached = cache.mget(cache_keys)

    miss_full_names: List[str] = []
    for full_name in repo_map:
        key = f"embedding:{full_name}"
        if key in cached and is_valid_embedding(cached[key]):
            results[full_name] = cached[key]
        else:
            miss_full_names.append(full_name)

    if not miss_full_names:
        return results

    client = get_openai_client()
    if client is None:
        logger.warning("OPENROUTER_API_KEY is not set; skipping remote embedding generation.")
        return results

    # Process misses in batches of 50
    newly_computed: Dict[str, List[float]] = {}
    batch_size = 50

    for i in range(0, len(miss_full_names), batch_size):
        batch_names = miss_full_names[i : i + batch_size]
        texts: List[str] = []
        for name in batch_names:
            r = repo_map[name]
            repo_name = r.get("name", "")
            desc = r.get("description") or ""
            lang = r.get("language") or ""
            text = f"{repo_name} {desc} {lang}".strip()
            # Truncate to 8000 chars as per spec
            texts.append(text[:8000])

        try:
            resp = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )
            for idx, item in enumerate(resp.data):
                fname = batch_names[idx]
                vector = item.embedding
                if is_valid_embedding(vector):
                    results[fname] = vector
                    newly_computed[f"embedding:{fname}"] = vector
        except Exception as e:
            logger.error("Failed to generate batch embeddings via OpenRouter: %s", e)

    if newly_computed:
        cache.mset(newly_computed, ttl=LONG_TTL)

    return results
