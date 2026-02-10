from pydantic import BaseModel


class KeywordSchema(BaseModel):
    article: str
    depth: int
    ignore_list: list[str]
    percentile: int
