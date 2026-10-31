"""Programming language color mapping and color utility functions for GitFlix.
"""

from typing import Dict, Optional

# Official and recognized branding colors for popular languages
LANGUAGE_COLORS: Dict[str, str] = {
    "Python": "#3776ab",
    "TypeScript": "#3178c6",
    "Rust": "#dea584",
    "Go": "#00add8",
    "JavaScript": "#f7df1e",
    "Ruby": "#701516",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Swift": "#ffac45",
    "Kotlin": "#A97BFF",
    "PHP": "#4F5D95",
    "Scala": "#c22d40",
    "Dart": "#00B4AB",
    "R": "#198CE7",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
}

DEFAULT_LANGUAGE_COLOR = "#808080"


def get_language_color(lang: Optional[str]) -> str:
    """Return the associated brand hex color for a language, or a default gray.

    Supports case-insensitive matching.
    """
    if not lang or not isinstance(lang, str):
        return DEFAULT_LANGUAGE_COLOR

    # Check exact match first
    if lang in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[lang]

    # Case-insensitive lookup
    lang_lower = lang.strip().lower()
    for name, hex_code in LANGUAGE_COLORS.items():
        if name.lower() == lang_lower:
            return hex_code

    return DEFAULT_LANGUAGE_COLOR
