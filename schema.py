from pydantic import BaseModel, Field, field_validator


class KeywordSchema(BaseModel):
    article: str = Field(
        ..., min_length=1, description="Wikipedia article title (not URL)"
    )
    depth: int = Field(..., ge=1, le=5, description="Traversal depth (1-5)")
    ignore_list: list[str] = Field(default_factory=list, description="Words to ignore")
    percentile: int = Field(
        ..., ge=0, le=100, description="Percentile threshold (0-100)"
    )

    @field_validator("article")
    @classmethod
    def validate_article(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Article title cannot be empty")

        if v.startswith("http://") or v.startswith("https://") or v.startswith("www."):
            raise ValueError(
                "Please provide article title only, not full URL. "
                "Example: 'Python' instead of 'https://hu.wikipedia.org/wiki/Python'"
            )

        return v.strip()
