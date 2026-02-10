from fastapi import FastAPI, Query
from schema import KeywordSchema

app = FastAPI()


@app.get("/word-frequency")
async def word_frequency(
    article: str = Query(...),
    depth: int = Query(...)
):
    """A word-frequency dictionary that includes the count
    and percentage frequency of each word found in the traversed articles."""

    raise NotImplementedError("Waiting for further implementation")


@app.post("/keywords")
async def keywords(params: KeywordSchema):
    """A dictionary similar to the one returned by /word-frequency,
    but excluding words in the ignore list and filtered by the specified percentile."""

    raise NotImplementedError("Waiting for further implementation")