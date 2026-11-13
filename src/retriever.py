"""RAG 파이프라인 (제출 규약 진입점).

실제 코드는 해석 지식 도메인 src/knowledge/retriever.py 에 있다. 제출 규약이 src/retriever.py 를 요구하므로 여기서 다시 내보낸다.
"""
from src.knowledge.retriever import load_chunks, search, similarity, split_features  # noqa: F401
from src.knowledge.schemas import Chunk  # noqa: F401
