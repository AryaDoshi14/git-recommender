"""Configuration constants and environment variables for GitFlix core logic.

Loads variables from .env if present.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# GitHub API configuration
GITHUB_API_URL: str = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "").strip()

# AI / OpenRouter configuration
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL: str = "openai/text-embedding-3-small"

# Upstash Redis configuration (optional)
UPSTASH_REDIS_REST_URL: str = os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
UPSTASH_REDIS_REST_TOKEN: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()

# Cache TTL constants (in seconds)
RESULT_TTL: int = 86400            # 24 hours for full profile recommendations
COLD_START_TTL: int = 300          # 5 minutes for cold start profiles (so newly starred repos show soon)
LONG_TTL: int = 7 * 86400          # 7 days (604,800 seconds) for repo languages and embeddings

# Pagination and algorithm constants
MAX_STARRED_PAGES: int = 3         # Max pages of starred repositories to fetch
PER_PAGE: int = 100                # GitHub per_page items
MAX_LANG_REPOS: int = 50           # Number of owned repos used to calculate language weights
COLD_START_THRESHOLD: int = 5      # Repos starred threshold below which user is considered cold start
