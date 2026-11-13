"""웹 API 스키마: POST /query 요청·응답 본문 (제출 규약)."""
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """요청 본문. image(base64)와 session_id 는 제출 규약에 없는 선택 필드다."""

    question: str
    image: str | None = None
    session_id: str | None = None


class QueryResponse(BaseModel):
    """응답 본문 (제출 규약)."""

    answer: str
    contexts: list[str]
    trace: list[str]
