import logging
from fastapi import FastAPI, Query, HTTPException
from schema import KeywordSchema


from src.wiki_client import WikiFrequencyCounter
from logging_config import setup_logging
from utils.filters import filter_by_ignore_list, filter_by_percentile

setup_logging(level=logging.INFO)

app = FastAPI()


@app.get("/word-frequency")
async def word_frequency(
    article: str = Query(
        ...,
        min_length=1,
        description="Wikipedia article title (e.g., 'Python', not URL)"
    ),
    depth: int = Query(
        ...,
        ge=1,
        le=5,
        description="Traversal depth (1-5)"
    )
):
    """A word-frequency dictionary that includes the count
    and percentage frequency of each word found in the traversed articles."""
    
    if article.startswith("http://") or article.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid article parameter",
                "message": "Please provide article title only, not full URL",
                "example": "Use 'Python' instead of 'https://hu.wikipedia.org/wiki/Python'"
            }
        )
    
    article = article.strip()
    if article.startswith("/wiki/"):
        article = article[6:]
    
    try:
        wiki = WikiFrequencyCounter(article, depth)
        result = await wiki.run()

        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Article not found or no content extracted",
                    "article": article,
                    "suggestion": "Please verify the article title and ensure it exists on Wikipedia"
                }
            )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logging.error(f"Error processing request for article '{article}' at depth {depth}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while processing your request"
            }
        )


@app.post("/keywords")
async def keywords(params: KeywordSchema):
    """A dictionary similar to the one returned by /word-frequency,
    but excluding words in the ignore list and filtered by the specified percentile."""

    raise NotImplementedError("Waiting for further implementation")