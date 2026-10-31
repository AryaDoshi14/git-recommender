# 🍿 GitFlix

**GitHub, but Netflix. Discover your next favorite repository with AI-powered recommendations.**

GitFlix transforms the way you discover open-source projects. Built for developers who want to find hidden gems, trending repositories, and projects perfectly tailored to their interests—all wrapped in an addictive, Netflix-style interface.

Instead of endlessly scrolling GitHub's generic trending page, GitFlix uses your GitHub profile, language usage, and vector embeddings (via OpenAI & OpenRouter) to curate personalized rows of repositories you're actually likely to star, contribute to, or use.

---

## ✨ Features

- 🎬 **Netflix-Style UI**: Beautiful, horizontally scrolling rows of repository recommendations with smooth scroll-snap and card hover effects.
- 🧠 **AI-Powered Discovery**: Uses OpenAI embeddings (`openai/text-embedding-3-small`) to analyze your starred repos and tech stack to find semantic matches.
- ⚡ **Multi-Tier Caching**: Thread-safe in-memory cache with TTL expiry, and optional Upstash Redis REST support to avoid rate limits and minimize recommendation latency.
- 📱 **Responsive & Clean**: Custom dark theme with Netflix aesthetics, glowing language tags, letter-initial avatars, and pulsing skeleton placeholders.
- 🔍 **Smart Fallbacks & Cold Starts**: If you have fewer than 5 stars, GitFlix seamlessly transitions to cold-start mode with curated popular and underrated projects in your primary language.

---

## 🛠️ Tech Stack

- **Framework**: [Streamlit](https://streamlit.io/) (Python 3.11+)
- **HTTP Client**: [Requests](https://requests.readthedocs.io/)
- **Vector Math**: [NumPy](https://numpy.org/)
- **AI / Embeddings**: [OpenRouter](https://openrouter.ai/) (via official [OpenAI Python SDK](https://github.com/openai/openai-python))
- **Environment**: [python-dotenv](https://github.com/theskumar/python-dotenv)
- **Testing**: [pytest](https://pytest.org/) & [responses](https://github.com/getsentry/responses)

---

## 📁 Project Structure

```text
gitflix/
├── app.py                  # Streamlit entry point (config, CSS, navbar, state switching)
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Pytest and package discovery configuration
├── .env.example            # Template for environment variables
├── .gitignore              # Git ignore rules for venv, cache, and secrets
├── .streamlit/
│   └── config.toml         # Streamlit dark theme (#0d0d0d, #1a1a1a, #7c3aed, #ffffff)
├── core/                   # Pure business logic (NO Streamlit dependencies)
│   ├── __init__.py
│   ├── config.py           # Configuration constants and environment loader
│   ├── errors.py           # Custom GitHubError with HTTP status & Retry-After
│   ├── github_client.py    # GitHub REST v3 client with error handling & pagination
│   ├── languages.py        # Language statistics, byte calculations & percentages
│   ├── embeddings.py       # OpenRouter embeddings client & cosine similarity
│   ├── cache.py            # Unified cache interface (In-memory TTL & Upstash Redis)
│   ├── recommender.py      # Recommendation engine (Cold start & 6-row vector pipeline)
│   └── orchestrator.py     # End-to-end profile loading with 25s timeout ceiling
├── ui/                     # Presentation layer (Pure HTML/CSS, NO GitHub API logic)
│   ├── __init__.py
│   ├── styles.py           # Unified Netflix-style CSS stylesheet
│   ├── colors.py           # Brand color mapping for 20+ programming languages
│   └── components.py       # Navbar, hero, cards, rows, banners, and skeleton
├── tests/                  # Pytest unit & smoke test suite
└── README.md
```

---

## 🏁 Getting Started

### Prerequisites

- Python 3.11 or higher
- A GitHub Personal Access Token (recommended to increase rate limits from 60 to 5,000 req/hr)
- An OpenRouter API Key (provides access to `openai/text-embedding-3-small`)
- *(Optional)* Upstash Redis REST credentials for distributed caching

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AryaDoshi14/gitflix.git
   cd gitflix
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your keys:
   ```env
   # GitHub (Increases API rate limits)
   GITHUB_TOKEN=your_github_personal_access_token

   # OpenRouter (Required for vector embedding calculations)
   OPENROUTER_API_KEY=your_openrouter_api_key

   # Optional: Upstash Redis (Automatically falls back to in-memory TTL cache if left empty)
   UPSTASH_REDIS_REST_URL=
   UPSTASH_REDIS_REST_TOKEN=
   ```

---

## 🚀 Running the App

Start the Streamlit application:

```bash
streamlit run app.py
```

Streamlit will launch local development server (typically at `http://localhost:8501`). Enter any public GitHub username (for example `torvalds`, `tiangolo`, or your own handle) and click **Explore**!

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
pytest -v
```

The test suite covers:
- Language byte aggregation and percentage sorting
- Cosine similarity vector edge cases (zero magnitude, NaN handling, dimension mismatches)
- Cross-row repository deduplication and empty row removal
- Cold-start threshold boundary conditions (4 stars vs. 5 stars)
- Partial results recovery on mid-loop GitHub rate limits (mocked with `responses`)
- GitHub API 404/403/429 error mapping
- HTML escaping against XSS in repository cards
- Streamlit `AppTest` smoke test verifying initial page rendering

---

## 🌐 Deployment to Streamlit Community Cloud

The app is fully configured for continuous deployment on [Streamlit Community Cloud](https://share.streamlit.io/):

1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io/).
3. Click **"New app"**, select your repository, branch (`main`), and set the main file path to `app.py`.
4. In **Advanced settings** -> **Secrets**, paste your configuration values:
   ```toml
   GITHUB_TOKEN = "your_github_token"
   OPENROUTER_API_KEY = "your_openrouter_api_key"
   # Optional:
   # UPSTASH_REDIS_REST_URL = "..."
   # UPSTASH_REDIS_REST_TOKEN = "..."
   ```
5. Click **Deploy!**

---

## 🤝 Contributing

Contributions are always welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License & Disclaimer

Built with Python, Streamlit, and OpenRouter. Not affiliated with GitHub or Netflix.
