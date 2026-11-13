"""풀이 스키마: 풀이 도구가 돌려주는 결과의 모양 (키 이름은 실제 JSON 키와 같다)."""
from typing import TypedDict

# 닮은 동물 하나 (육지·해상·공중 중 하나)
AnimalPick = TypedDict("AnimalPick", {"구분": str, "동물": str, "닮은 이유": str})

# find_similar_animals 결과
AnimalsResult = TypedDict("AnimalsResult", {"animals": list[AnimalPick], "contexts": list[str]})

# find_similar_king 결과. image 는 /static/kings/… 어진 그림 경로이며 원본 어진이 없으면 빈 문자열
KingPick = TypedDict(
    "KingPick",
    {"found": bool, "왕": str, "관상 유형": str, "업적": str, "닮은 점": str, "image": str, "contexts": list[str]},
)

# search_reading_docs 결과
ReadingDocsResult = TypedDict("ReadingDocsResult", {"found": bool, "contexts": list[str]})
