"""운세 도구: get_fortune."""
from datetime import date, datetime, timedelta

from langchain_core.tools import tool

from src.fortune.schemas import DayFortune, FortuneResult
from src.knowledge.retriever import load_chunks, similarity
from src.knowledge.traits import best_types, type_name
from src.shared.config import KST
from src.shared.messages import to_json

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def season_of(month: int) -> str:
    """월로 계절 이름을 정한다."""
    return {12: "겨울", 1: "겨울", 2: "겨울", 3: "봄", 4: "봄", 5: "봄", 6: "여름", 7: "여름", 8: "여름"}.get(month, "가을")


@tool
def get_fortune(features: list[str], day: str = "") -> str:
    """날짜와 얼굴 특징으로 오늘의 운세, 이번 주 날짜별 흐름, 계절 운세, 성공운을 만든다.

    features 는 얼굴 특징 목록, day 는 'YYYY-MM-DD' (비우면 오늘). 운세는 재미 문구이며 저장하지 않는다.
    """
    today = date.fromisoformat(day) if day else datetime.now(KST).date()
    sections = {c.title: c for c in load_chunks("fortune.md")}

    daily = sections["오늘의 운세 · 기운 문구"].fields
    daily_line = daily[today.toordinal() % len(daily)][1]
    feature_lines = []
    for f in features:
        key, line = max(sections["오늘의 운세 · 특징별 한마디"].fields, key=lambda kv: similarity(f, kv[0]))
        if similarity(f, key) >= 0.3 and line not in feature_lines:
            feature_lines.append(line)

    week_fields = dict(sections["이번 주 운세 · 요일별 흐름"].fields)
    monday = today - timedelta(days=today.weekday())
    week: list[DayFortune] = [
        {"날짜": (monday + timedelta(days=i)).isoformat(), "요일": WEEKDAYS[i], "운세": week_fields[WEEKDAYS[i]]}
        for i in range(7)
    ]

    season_name = season_of(today.month)
    season = dict(sections[f"계절 운세 · {season_name}"].fields)

    types = best_types(features)
    success = dict(sections["성공운 · 유형별 한마디"].fields).get(type_name(types[0]), "") if types else ""

    used = ["오늘의 운세 · 기운 문구", "오늘의 운세 · 특징별 한마디", "이번 주 운세 · 요일별 흐름",
            f"계절 운세 · {season_name}", "성공운 · 유형별 한마디"]
    result: FortuneResult = {
        "날짜": today.isoformat(),
        "오늘": {"기운": daily_line, "특징별": feature_lines},
        "이번 주": week,
        "계절": {"지금 계절": season_name, **season},
        "성공운": success,
        "contexts": [sections[t].as_context() for t in used],
    }
    return to_json(result)
