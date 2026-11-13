"""해석 지식 스키마: 해석 문서의 한 섹션(Chunk)."""
from dataclasses import dataclass, field

MATCH_KEYS = ("키워드", "연결 특징")  # 검색에 쓰는 필드


@dataclass
class Chunk:
    """해석 문서의 한 섹션."""

    source: str
    title: str
    body: str
    fields: list[tuple[str, str]] = field(default_factory=list)

    def get(self, key: str) -> str:
        """필드 값을 이름으로 꺼낸다. 없으면 빈 문자열."""
        return next((v for k, v in self.fields if k == key), "")

    def match_text(self) -> str:
        """검색에 쓰는 글: 제목과 키워드·연결 특징."""
        return " ".join([self.title, *(self.get(k) for k in MATCH_KEYS)])

    def as_context(self) -> str:
        """응답 contexts 에 넣을 근거 문장."""
        return f"[{self.source} · {self.title}]\n{self.body}"
