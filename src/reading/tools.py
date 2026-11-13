"""풀이 도구: search_reading_docs, find_similar_animals, find_similar_king."""
import hashlib

from langchain_core.tools import tool

from src.knowledge.retriever import load_chunks, search, similarity, split_features
from src.knowledge.traits import best_types, type_name
from src.reading.schemas import AnimalPick, AnimalsResult, KingPick, ReadingDocsResult
from src.shared.config import STATIC_DIR
from src.shared.messages import to_json

GROUPS = ("육지", "해상", "공중")

# 원본 어진(퍼블릭 도메인, Wikimedia Commons) 그림 파일이 있는 왕. kings.md 에 경로가 없어도 파일이 있으면 이 경로를 쓴다
PORTRAIT_FILES = {
    "태조": "/static/kings/taejo.jpg",      # 경기전 소장 1872년 모사본
    "영조": "/static/kings/yeongjo.jpg",    # 1900년 모사본
    "철종": "/static/kings/cheoljong.jpg",  # 1861년 작, 일부 소실
    "고종": "/static/kings/gojong.jpg",     # 채용신 작, 20세기 초
}


@tool
def search_reading_docs(query: str) -> str:
    """해석 문서에서 얼굴 특징에 맞는 부위별 풀이와 성향 유형(강점·약점·성격·재능·잠재력·성장 방향)을 찾는다.

    query 에는 '넓은 이마, 올라간 눈꼬리, 곧은 콧대' 처럼 특징을 쉼표로 나눠 적는다.
    문서에 없는 특징은 결과에 나오지 않는다. 그런 특징은 풀이를 지어내지 말고 자료에 없다고 안내한다.
    """
    features = split_features(query)
    parts = search(query, ("face_parts.md",))
    types = best_types(features) if parts else []
    found = parts + types
    if not found:
        return to_json({"found": False, "message": "해석 자료에 맞는 내용이 없다.", "contexts": []})
    result: ReadingDocsResult = {"found": True, "contexts": [c.as_context() for c in found]}
    return to_json(result)


@tool
def find_similar_animals(features: list[str]) -> str:
    """얼굴 특징으로 육지·해상·공중(새)에서 닮은 동물을 하나씩 고르고 닮은 이유를 돌려준다.

    features 는 ['올라간 눈꼬리', '올라간 입꼬리'] 처럼 특징 목록이다. 좋은 인상으로만 비유한다.
    """
    best: dict[str, tuple[float, object]] = {}
    for chunk in load_chunks("animals.md"):
        links = [s.strip() for s in chunk.get("연결 특징").split(",")]
        score = sum(max(similarity(f, link) for link in links) for f in features)
        group = chunk.get("구분")
        if group not in best or score > best[group][0]:
            best[group] = (score, chunk)
    animals: list[AnimalPick] = []
    for group in GROUPS:
        if group in best:
            chunk = best[group][1]
            animals.append({"구분": group, "동물": chunk.title.split("·")[-1].strip(), "닮은 이유": chunk.get("닮은 이유")})
    result: AnimalsResult = {"animals": animals, "contexts": [best[g][1].as_context() for g in GROUPS if g in best]}
    return to_json(result)


def _file_exists(path: str) -> bool:
    """/static/… 경로의 그림 파일이 실제로 있는지 본다."""
    return bool(path) and (STATIC_DIR / path.removeprefix("/static/")).is_file()


def _portrait_path(king) -> str:
    """어진 그림 경로를 정한다. kings.md 의 어진 필드를 먼저 보고, 없으면 PORTRAIT_FILES 에서 왕 이름으로 찾는다.

    그림 파일이 실제로 없으면 깨진 이미지 대신 빈 값을 돌려준다.
    """
    portrait = king.get("어진")
    from_doc = portrait.split()[0] if portrait.startswith("/static/") else ""
    if _file_exists(from_doc):
        return from_doc
    from_code = PORTRAIT_FILES.get(king.title.split("·")[-1].strip(), "")
    return from_code if _file_exists(from_code) else ""


def _king_context(king, image: str) -> str:
    """닮은 왕의 근거 문장. 그림 경로가 문서에 없으면 한 줄 덧붙여 화면이 어진 그림을 찾을 수 있게 한다."""
    context = king.as_context()
    return context if not image or image in context else f"{context}\n- 어진 그림: {image}"


@tool
def find_similar_king(features: list[str]) -> str:
    """얼굴 특징으로 관상 유형(성향)이 닮은 조선의 왕을 고르고, 업적과 닮은 점, 어진 그림 경로를 돌려준다.

    features 는 ['넓은 이마', '곧은 콧대'] 처럼 특징 목록이다. 얼굴 생김새가 닮았다는 뜻이 아니라 성향이 닮았다는 비유다.
    어진(초상화)이 남아 있지 않은 왕은 image 가 비어 있다.
    """
    types = best_types(features)
    if not types:
        return to_json({"found": False, "message": "특징으로 성향 유형을 정하지 못했다.", "contexts": []})
    name = type_name(types[0])
    candidates = [c for c in load_chunks("kings.md") if c.get("연결 유형") == name]
    if not candidates:
        return to_json({"found": False, "message": "맞는 왕을 찾지 못했다.", "contexts": []})
    # 같은 유형의 왕이 여럿이면 특징으로 정해지는 순번으로 고른다 (같은 얼굴이면 늘 같은 왕)
    key = "|".join(sorted(f.strip() for f in features))
    king = candidates[int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % len(candidates)]
    image = _portrait_path(king)
    result: KingPick = {
        "found": True,
        "왕": king.title.split("·")[-1].strip(),
        "관상 유형": name,
        "업적": king.get("업적"),
        "닮은 점": king.get("닮은 점"),
        "image": image,
        "contexts": [types[0].as_context(), _king_context(king, image)],
    }
    return to_json(result)
