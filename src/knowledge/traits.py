"""성향 유형 고르기: 얼굴 특징으로 traits.md 의 관상 유형(기획가·소통가 등)을 정한다. 풀이·닮은 왕·성공운이 함께 쓴다."""
from src.knowledge.retriever import load_chunks, similarity
from src.knowledge.schemas import Chunk


def best_types(features: list[str], top: int = 1) -> list[Chunk]:
    """얼굴 특징과 연결 특징이 가장 많이 겹치는 성향 유형을 고른다."""
    scored = []
    for chunk in load_chunks("traits.md"):
        links = [s.strip() for s in chunk.get("연결 특징").split(",")]
        score = sum(max(similarity(f, link) for link in links) for f in features)
        scored.append((score, chunk))
    scored.sort(key=lambda x: -x[0])
    return [c for s, c in scored[:top] if s > 0]


def type_name(chunk: Chunk) -> str:
    """유형 섹션 제목에서 유형 이름만 꺼낸다 (예: '유형 · 큰 그림을 그리는 기획가' → '기획가')."""
    return chunk.title.split("·")[-1].strip().split()[-1]
