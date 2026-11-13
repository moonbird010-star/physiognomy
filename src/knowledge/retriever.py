"""RAG 파이프라인: data/ 의 해석 문서를 섹션(##) 단위로 잘라 키워드로 찾는다."""
import re
from functools import lru_cache

from src.knowledge.schemas import Chunk
from src.shared.config import DATA_DIR

MIN_SCORE = 0.3


def _bigrams(text: str) -> set[str]:
    """공백·기호를 뺀 글자 두 개씩 묶음을 만든다."""
    s = re.sub(r"[^0-9a-z가-힣]", "", text.lower())
    return {s[i : i + 2] for i in range(len(s) - 1)} or ({s} if s else set())


def similarity(query: str, target: str) -> float:
    """query 의 글자 묶음 중 target 에도 있는 비율 (0~1)."""
    q = _bigrams(query)
    return len(q & _bigrams(target)) / len(q) if q else 0.0


@lru_cache(maxsize=None)
def load_chunks(filename: str) -> tuple[Chunk, ...]:
    """data/ 의 마크다운 문서 하나를 ## 섹션 단위 Chunk 로 나눈다."""
    text = (DATA_DIR / filename).read_text(encoding="utf-8")
    chunks = []
    for part in text.split("\n## ")[1:]:
        title, _, body = part.partition("\n")
        body = body.strip()
        fields = []
        for line in body.splitlines():
            m = re.match(r"^-\s*([^:]+):\s*(.+)$", line.strip())
            if m:
                fields.append((m.group(1).strip(), m.group(2).strip()))
        chunks.append(Chunk(f"data/{filename}", title.strip(), body, fields))
    return tuple(chunks)


def split_features(query: str) -> list[str]:
    """여러 특징이 섞인 질의를 쉼표·세미콜론·줄바꿈으로 나눈다."""
    return [p.strip() for p in re.split(r"[,;/\n]|그리고", query) if p.strip()]


def search(query: str, files: tuple[str, ...], per_feature: int = 1) -> list[Chunk]:
    """특징마다 가장 잘 맞는 섹션을 찾는다. 점수가 낮으면 버린다 (지어내지 않기 위해)."""
    pool = [c for f in files for c in load_chunks(f)]
    found: list[Chunk] = []
    for feature in split_features(query):
        scored = sorted(((similarity(feature, c.match_text()), c) for c in pool), key=lambda x: -x[0])
        for score, chunk in scored[:per_feature]:
            if score >= MIN_SCORE and chunk not in found:
                found.append(chunk)
    return found
