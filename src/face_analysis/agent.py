"""사진 분석 서브 에이전트: 감독 에이전트가 사진 분석을 맡기는 photo_agent."""
from functools import lru_cache

from langchain_core.tools import tool

from src.face_analysis.prompts import PHOTO_AGENT_PROMPT
from src.face_analysis.tools import analyze_face_photo
from src.shared.delegation import build_subagent, delegate


@lru_cache(maxsize=1)
def _subagent():
    """사진 분석 서브 에이전트를 한 번만 만든다."""
    return build_subagent([analyze_face_photo], PHOTO_AGENT_PROMPT)


@tool
def photo_agent() -> str:
    """사진 분석 담당 서브 에이전트에게 첨부 사진 분석을 맡긴다. 인자는 없다 (사진은 서버가 넘겨준다).

    결과의 status 가 ok 면 이마·눈·코·입·귀 특징이 온다. ok 가 아니면 풀이하지 말고 안내만 한다.
    """
    return delegate(_subagent(), "photo_agent", "첨부된 사진을 분석해 결과를 보고해 줘.")
