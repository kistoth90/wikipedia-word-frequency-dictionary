import httpx
import logging
import re
from collections import Counter
from fastapi import status
from bs4 import BeautifulSoup

from constants import HEADERS

URL_PREFIX = "https://hu.wikipedia.org/wiki/"


class WikiFrequencyCounter:
    def __init__(self, article: str, depth: int):
        self.article = article
        self.depth = depth

        self.counter = 0
        self.articles = {self.article: False}
        self.collected_words = []
        self.word_frequency = {}

    async def get_article_source(self, article: str):
        async with httpx.AsyncClient(headers=HEADERS) as client:
            logging.debug(f"Get article source: {article}")
            r = await client.get(f"{URL_PREFIX}{article}")

            if r.status_code != status.HTTP_200_OK:
                self.articles.pop(article)
                logging.error(f"Article not found: {article}, status: {r.status_code}")

            self.articles[article] = True
            self.counter += 1
            return r.text

    def extract_words_from_html(self, html_text: str) -> None:
        soup = BeautifulSoup(html_text, "html.parser")

        body_content = soup.find("div", id="mw-content-text")

        if not body_content:
            logging.warning("mw-content-text div not found in HTML")
            return

        text = body_content.get_text()

        words = re.findall(r"\b[a-záéíóöőúüűA-ZÁÉÍÓÖŐÚÜŰ]+\b", text)

        # Add words to collected_words
        self.collected_words.extend(words)

        logging.debug(f"Extracted {len(words)} words from article")

    def calculate_frequency(self) -> dict[str, dict[str, float | int]]:
        if not self.collected_words:
            logging.warning("No words collected to calculate frequency")
            return {}

        word_counts = Counter(word.lower() for word in self.collected_words)

        total_words = len(self.collected_words)

        frequency_dict = {
            word: {"count": count, "percentage": round((count / total_words) * 100, 4)}
            for word, count in word_counts.items()
        }

        logging.info(
            f"Calculated frequency for {len(frequency_dict)} unique words from {total_words} total words"
        )
        return frequency_dict

    async def run(self):
        while self.counter < self.depth:
            unprocessed = [
                article for article, processed in self.articles.items() if not processed
            ]
            if not unprocessed:
                break

            act_article = unprocessed[0]
            html_text = await self.get_article_source(act_article)

            self.extract_words_from_html(html_text)

        self.word_frequency = self.calculate_frequency()

        return self.word_frequency
