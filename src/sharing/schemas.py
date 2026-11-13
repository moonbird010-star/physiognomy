"""공유 스키마: 메일 공유 요청 본문 (POST /share-email)."""
from pydantic import BaseModel


class ShareRequest(BaseModel):
    """메일 공유 요청: 받는 주소, 결과 HTML(사진 제외), 본문에 넣을 짧은 요약."""

    email: str
    html: str
    summary: str = ""
