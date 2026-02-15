import httpx
import logging
import re
import time
import asyncio
from collections import Counter
from fastapi import status
from bs4 import BeautifulSoup
from urllib.parse import unquote

from config import HEADERS, get_article_url, REQUEST_TIMEOUT, MAX_CONCURRENT_REQUESTS

WORD_PATTERN = re.compile(r"\b[a-záéíóöőúüűA-ZÁÉÍÓÖŐÚÜŰ]+\b")


class WikiFrequencyCounter:
    def __init__(self, article: str, depth: int):
        self.article = article
        self.depth = depth
        self.word_counter = (
            Counter()
        )  # Use Counter directly for better memory efficiency
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._client: httpx.AsyncClient | None = None

    async def _open_client(self):
        self._client = httpx.AsyncClient(headers=HEADERS, timeout=REQUEST_TIMEOUT)

    async def _close_client(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_article_source(self, article: str) -> str | None:
        """Fetch Wikipedia article HTML"""
        fetch_start = time.time()
        try:
            logging.debug(f"Fetching article: {article}")
            article_url = get_article_url(article)
            r = await self._client.get(article_url)

            if r.status_code == status.HTTP_404_NOT_FOUND:
                logging.warning(f"Article not found: {article}")
                return None

            if r.status_code != status.HTTP_200_OK:
                logging.error(
                    f"Error fetching article {article}: status {r.status_code}"
                )
                return None

            fetch_time = time.time() - fetch_start
            logging.info(
                f"Fetched '{article}' in {fetch_time:.3f}s (size: {len(r.text)/1024:.1f}KB)"
            )
            return r.text

        except httpx.TimeoutException:
            logging.error(f"Timeout fetching article: {article}")
            return None
        except httpx.HTTPError as e:
            logging.error(f"HTTP error fetching {article}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching {article}: {e}")
            return None

    def _extract_links_from_soup(self, body_content) -> list[str]:
        """Extract Wikipedia article links from parsed soup content.

        Args:
            body_content: BeautifulSoup element for mw-content-text div

        Returns:
            List of article titles (URL-decoded, without /wiki/ prefix)
        """
        # Remove navbox, infobox, noprint, and noviewer elements before extracting links
        for element in body_content.find_all(
            class_=lambda x: x
            and any(
                cls in x.lower() for cls in ["navbox", "infobox", "noprint", "noviewer"]
            )
        ):
            element.decompose()

        links = set()  # Use set to avoid duplicates

        for link in body_content.find_all("a", href=True):
            href = link["href"]

            # Handle both relative (/wiki/...) and absolute (https://...wikipedia.org/wiki/...) links
            article_title = None

            if href.startswith("/wiki/"):
                # Relative link
                article_title = href[6:]
            elif "/wiki/" in href and (
                "wikipedia.org" in href or "wikipédia" in href.lower()
            ):
                # Absolute Wikipedia link
                wiki_index = href.find("/wiki/")
                article_title = href[wiki_index + 6 :]
            else:
                # Not a Wikipedia article link
                continue

            # Skip if only a fragment
            if href.startswith("#"):
                continue

            # Skip if contains # (fragments) - remove fragment part
            if "#" in article_title:
                article_title = article_title.split("#")[0]
                if not article_title:  # Was only a fragment
                    continue

            # Skip if contains ? (query parameters) - remove query part
            if "?" in article_title:
                article_title = article_title.split("?")[0]
                if not article_title:
                    continue

            # URL decode the title
            decoded_title = unquote(article_title)

            # Skip if contains : (special pages like File:, Special:, etc.)
            if ":" in decoded_title:
                continue

            # Skip empty titles
            if not decoded_title.strip():
                continue

            links.add(decoded_title)

        logging.debug(f"Extracted {len(links)} unique links from article")
        return list(links)

    def extract_words_and_links(
        self, html_text: str, need_links: bool
    ) -> tuple[Counter, list[str]]:
        """Parse HTML once, extract words and optionally links.

        Thread-safe: returns a Counter instead of mutating shared state.

        Args:
            html_text: Raw HTML content
            need_links: Whether to extract links for next depth level

        Returns:
            Tuple of (word_counter, links)
        """
        parse_start = time.time()
        soup = BeautifulSoup(html_text, "lxml")

        body_content = soup.find("div", id="mw-content-text")

        if not body_content:
            logging.warning("mw-content-text div not found in HTML")
            return Counter(), []

        # Extract links BEFORE decomposing tables (tables contain valid links)
        links = self._extract_links_from_soup(body_content) if need_links else []

        # Remove script, style, navigation, and non-content elements
        for element in body_content.find_all(["script", "style", "nav", "table"]):
            element.decompose()

        # Remove elements with noprint and noviewer classes (navigation, metadata, etc.)
        for element in body_content.find_all(
            class_=lambda x: x
            and any(cls in x.lower() for cls in ["noprint", "noviewer"])
        ):
            element.decompose()

        # Get text with separator to avoid word concatenation
        text = body_content.get_text(separator=" ", strip=True)

        words = WORD_PATTERN.findall(text)
        word_counter = Counter(word.lower() for word in words)

        parse_time = time.time() - parse_start
        logging.info(f"Extracted {len(words)} words in {parse_time:.3f}s")

        return word_counter, links

    def calculate_frequency(self) -> dict[str, dict[str, float | int]]:
        """Calculate word frequency from word counter.

        Returns:
            Dictionary with word frequencies including count and percentage
        """
        if not self.word_counter:
            logging.warning("No words collected to calculate frequency")
            return {}

        total_words = sum(self.word_counter.values())

        frequency_dict = {
            word: {"count": count, "percentage": round((count / total_words) * 100, 4)}
            for word, count in self.word_counter.items()
        }

        logging.info(
            f"Calculated frequency for {len(frequency_dict)} unique words from {total_words} total words"
        )
        return frequency_dict

    async def process_article(
        self, article: str, current_depth: int
    ) -> tuple[str, bool, list[str]]:
        """Process a single article: fetch HTML, extract words and links.

        Args:
            article: Article title to process
            current_depth: Current depth level (for determining if we need links)

        Returns:
            Tuple of (article_title, success, links_for_next_level)
        """
        article_start = time.time()

        # Use semaphore to limit concurrent requests
        async with self._semaphore:
            # Fetch article HTML
            html_text = await self.get_article_source(article)

        if html_text is None:
            logging.warning(f"Skipping article {article} due to fetch error")
            return (article, False, [])

        # Offload CPU-bound HTML parsing to thread pool
        need_links = current_depth < self.depth - 1
        loop = asyncio.get_running_loop()
        word_counter, links = await loop.run_in_executor(
            None, self.extract_words_and_links, html_text, need_links
        )

        # Merge counter on the event loop thread (single-threaded, safe)
        self.word_counter += word_counter

        if need_links:
            logging.debug(f"Found {len(links)} links in {article} for next depth level")

        article_time = time.time() - article_start
        logging.info(f"Processed article '{article}' in {article_time:.3f}s")

        return (article, True, links)

    async def run(self) -> dict:
        """Process articles up to specified depth using breadth-first traversal with concurrent fetching."""
        overall_start = time.time()
        current_depth = 0
        current_level = [self.article]  # Articles to process at current depth
        visited = set()  # Track all visited articles

        await self._open_client()
        try:
            while current_depth < self.depth and current_level:
                level_start = time.time()

                # Filter out already visited articles
                articles_to_process = [
                    article for article in current_level if article not in visited
                ]

                # Mark as visited
                visited.update(articles_to_process)

                logging.info(
                    f"Starting depth level {current_depth + 1} with {len(articles_to_process)} articles to process concurrently"
                )

                # Process all articles at this level concurrently
                tasks = [
                    self.process_article(article, current_depth)
                    for article in articles_to_process
                ]
                results = await asyncio.gather(*tasks)

                # Collect links for next level
                next_level = []
                for article, success, links in results:
                    if success:
                        next_level.extend(links)

                current_depth += 1
                current_level = next_level
                level_time = time.time() - level_start
                logging.info(
                    f"Completed depth level {current_depth} in {level_time:.2f}s, found {len(next_level)} articles for next level"
                )
        finally:
            await self._close_client()

        calc_start = time.time()
        word_frequency = self.calculate_frequency()
        calc_time = time.time() - calc_start

        total_time = time.time() - overall_start
        logging.info(
            f"Total execution time: {total_time:.2f}s (frequency calculation: {calc_time:.3f}s)"
        )
        return word_frequency
