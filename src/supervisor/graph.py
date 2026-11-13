"""메인 에이전트 그래프: 감독(Supervisor) 에이전트가 서브 에이전트에게 일을 나눠 맡기고, checkpointer 로 대화를 기억한다.

.env 의 AGENT_MODE=single 이면 서브 에이전트 없이 도구를 직접 쓰는 단일 에이전트로 동작한다 (되돌리기용).
"""
import json
import os
import uuid
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from src.face_analysis.agent import photo_agent
from src.face_analysis.image import CURRENT_IMAGE, decode_image, image_from_notation
from src.face_analysis.tools import analyze_face_photo
from src.fortune.agent import fortune_agent
from src.fortune.tools import get_fortune
from src.guardrails.middleware import build_middleware
from src.reading.agent import reading_agent
from src.reading.tools import find_similar_animals, find_similar_king, search_reading_docs
from src.shared.config import KST
from src.shared.delegation import TURN_LOG
from src.shared.llm import chat_model, fallback_middleware
from src.shared.messages import message_text
from src.supervisor.prompts import SYSTEM_PROMPT, supervisor_prompt
from src.supervisor.schemas import QueryResult

SUPERVISOR_TOOLS = [photo_agent, reading_agent, fortune_agent]  # 감독 모드: 서브 에이전트에게 위임
DOMAIN_TOOLS = [analyze_face_photo, search_reading_docs, find_similar_animals, find_similar_king, get_fortune]  # 단일 모드
CONTEXT_TOOLS = {"search_reading_docs", "find_similar_animals", "find_similar_king", "get_fortune"}


def mode() -> str:
    """에이전트 구성: supervisor(기본) 또는 single."""
    return os.getenv("AGENT_MODE", "supervisor").strip().lower()


def build_agent():
    """가드레일·미들웨어와 메모리(checkpointer)를 붙인 관상 에이전트 그래프를 만든다 (기본: 감독 + 서브 에이전트)."""
    today = datetime.now(KST).date().isoformat()
    model = chat_model()
    single = mode() == "single"
    return create_agent(
        model=model,
        tools=DOMAIN_TOOLS if single else SUPERVISOR_TOOLS,
        system_prompt=(SYSTEM_PROMPT if single else supervisor_prompt()).format(today=today),
        middleware=build_middleware(model, fallback_middleware()),
        checkpointer=InMemorySaver(),
    )


_AGENT = None


def get_agent():
    """에이전트를 한 번만 만들어 재사용한다 (대화 메모리를 유지하기 위해)."""
    global _AGENT
    if _AGENT is None:
        _AGENT = build_agent()
    return _AGENT


def ask(question: str, image_b64: str | None = None, session_id: str | None = None) -> QueryResult:
    """질문(과 사진)을 받아 answer, contexts, trace 를 돌려준다. 사진은 이 함수 안에서만 쓴다."""
    image = decode_image(image_b64)
    if image is None:  # 사진 필드가 비어 있으면, 인-아웃 세트의 [사진:images/…] 표기로 보낸 경우를 대비해 읽어 본다
        question, image = image_from_notation(question)
    text = f"[사진 첨부됨]\n{question}" if image is not None else question
    config = {"configurable": {"thread_id": session_id or str(uuid.uuid4())}}

    log = {"trace": [], "contexts": []}  # 서브 에이전트 안쪽 도구 호출이 여기에 모인다
    image_token, log_token = CURRENT_IMAGE.set(image), TURN_LOG.set(log)
    try:
        state = get_agent().invoke({"messages": [HumanMessage(text)]}, config=config)
    finally:
        CURRENT_IMAGE.reset(image_token)
        TURN_LOG.reset(log_token)

    messages = state["messages"]
    last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
    turn = messages[last_human + 1 :]

    if mode() == "single":
        trace = [call["name"] for m in turn if isinstance(m, AIMessage) for call in m.tool_calls]
        contexts: list[str] = []
        for m in turn:
            if isinstance(m, ToolMessage) and m.name in CONTEXT_TOOLS:
                try:
                    contexts.extend(json.loads(m.content).get("contexts", []))
                except (json.JSONDecodeError, AttributeError):
                    pass
    else:
        trace, contexts = log["trace"], log["contexts"]  # 예: photo_agent, analyze_face_photo, reading_agent, …
    answer = next((message_text(m.content) for m in reversed(turn)
                   if isinstance(m, AIMessage) and message_text(m.content)), "")
    return {"answer": answer, "contexts": contexts, "trace": trace}
