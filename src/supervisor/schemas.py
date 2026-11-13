"""감독 스키마: ask() 가 돌려주는 응답 (제출 규약: answer, contexts, trace)."""
from typing import TypedDict


class QueryResult(TypedDict):
    """POST /query 응답 본문."""

    answer: str  # 최종 답 (마크다운, 마지막 줄에 재미 안내)
    contexts: list[str]  # 근거로 쓴 해석 문서 섹션 ("[data/파일 · 제목]\n본문")
    trace: list[str]  # 부른 서브 에이전트와 도구 이름 (예: photo_agent, analyze_face_photo, reading_agent, …)
