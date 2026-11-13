"""운세 스키마: get_fortune 이 돌려주는 결과의 모양 (키 이름은 실제 JSON 키와 같다)."""
from typing import TypedDict

# 이번 주 하루의 운세. 날짜는 YYYY-MM-DD
DayFortune = TypedDict("DayFortune", {"날짜": str, "요일": str, "운세": str})

# 오늘 운세: 날짜로 고른 기운 문구 + 얼굴 특징별 한마디
TodayFortune = TypedDict("TodayFortune", {"기운": str, "특징별": list[str]})

# get_fortune 결과. 계절은 {"지금 계절": 이름, "흐름": 문장, "연애": 문장}
FortuneResult = TypedDict(
    "FortuneResult",
    {"날짜": str, "오늘": TodayFortune, "이번 주": list[DayFortune], "계절": dict, "성공운": str, "contexts": list[str]},
)
