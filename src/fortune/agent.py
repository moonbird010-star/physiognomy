"""운세 서브 에이전트: 감독 에이전트가 운세를 맡기는 fortune_agent."""
from functools import lru_cache

from langchain_core.tools import tool

from src.fortune.prompts import FORTUNE_AGENT_PROMPT
from src.fortune.tools import get_fortune
from src.shared.delegation import build_subagent, delegate


@lru_cache(maxsize=1)
def _subagent():
    """운세 서브 에이전트를 한 번만 만든다."""
    return build_subagent([get_fortune], FORTUNE_AGENT_PROMPT)


@tool
def fortune_agent(request: str) -> str:
    """운세 담당 서브 에이전트에게 맡긴다: 오늘 운세, 이번 주 날짜별 흐름, 계절 운세, 성공운.

    request 에는 얼굴 특징(한국어)을 적는다. 예: "특징: 넓은 이마, 크고 동그란 눈"
    """
    return delegate(_subagent(), "fortune_agent", request)
