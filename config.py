import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

WIKIPEDIA_LANG = os.getenv("WIKIPEDIA_LANG", "en")
WIKIPEDIA_DOMAIN = f"https://{WIKIPEDIA_LANG}.wikipedia.org"

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

MAX_DEPTH = int(os.getenv("MAX_DEPTH", "5"))
MIN_DEPTH = 1

USER_AGENT = os.getenv(
    "USER_AGENT",
    "WikiFrequencyDictionary/1.0 (https://github.com/kistoth90/wikipedia-word-frequency-dictionary; csabitoth@gmail.com)",
)

HEADERS = {"User-Agent": USER_AGENT}


def get_article_url(article: str) -> str:
    """Construct Wikipedia article URL."""

    encoded_article = article.replace(" ", "_")
    return f"{WIKIPEDIA_DOMAIN}/wiki/{encoded_article}"
