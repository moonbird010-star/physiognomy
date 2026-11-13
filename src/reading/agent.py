"""풀이 서브 에이전트: 감독 에이전트가 부위별 풀이·닮은 왕·닮은 동물을 맡기는 reading_agent."""
from functools import lru_cache

from langchain_core.tools import tool

from src.reading.prompts import READING_AGENT_PROMPT
from src.reading.tools import find_similar_animals, find_similar_king, search_reading_docs
from src.shared.delegation import build_subagent, delegate


@lru_cache(maxsize=1)
def _subagent():
    """풀이 서브 에이전트를 한 번만 만든다."""
    return build_subagent([search_reading_docs, find_similar_king, find_similar_animals], READING_AGENT_PROMPT)


@tool
def reading_agent(request: str) -> str:
    """풀이 담당 서브 에이전트에게 맡긴다: 부위별 풀이, 강점·약점, 성격·재능·잠재력, 닮은 조선의 왕, 닮은 동물.

    request 에는 얼굴 특징(한국어)과 필요한 항목을 적는다. 예: "특징: 넓은 이마, 곧은 콧대 / 요청: 전체 풀이"
    """
    return delegate(_subagent(), "reading_agent", request)
