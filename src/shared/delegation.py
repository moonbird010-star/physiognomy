"""서브 에이전트 위임 도구: 서브 에이전트를 만들고, 일을 맡긴 뒤 안쪽 도구 호출·근거를 감독 쪽 기록(TURN_LOG)에 모은다.

사진 분석·풀이·운세 서브 에이전트가 함께 쓴다.
"""
import json
from contextvars import ContextVar

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.shared.llm import chat_model, fallback_middleware
from src.shared.messages import message_text

# 한 요청 동안 서브 에이전트 안에서 일어난 도구 호출과 근거를 모으는 칸 (응답의 trace·contexts 용)
TURN_LOG: ContextVar[dict | None] = ContextVar("TURN_LOG", default=None)


def build_subagent(tools: list, prompt: str):
    """서브 에이전트를 만든다. 대화 메모리는 두지 않는다 (감독 에이전트만 기억한다). 재시도·예비 모델은 붙인다."""
    return create_agent(
        model=chat_model(),
        tools=tools,
        system_prompt=prompt,
        middleware=[ModelRetryMiddleware(max_retries=2, initial_delay=2.0), *fallback_middleware()],
    )


def without_contexts(raw: str) -> str:
    """도구 원본 결과에서 긴 근거 문장(contexts)을 빼고 감독에게 넘긴다 (근거는 응답 contexts 로 따로 모은다)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    data.pop("contexts", None)
    return json.dumps(data, ensure_ascii=False)


def delegate(subagent, name: str, request: str) -> str:
    """서브 에이전트에게 일을 맡기고, 안에서 부른 도구 이름·근거를 TURN_LOG 에 남긴 뒤 보고서를 돌려준다."""
    state = subagent.invoke({"messages": [HumanMessage(request)]})
    messages = state["messages"]
    inner_trace = [call["name"] for m in messages if isinstance(m, AIMessage) for call in m.tool_calls]
    contexts, raws = [], []
    for m in messages:
        if isinstance(m, ToolMessage):
            raws.append(f"{m.name}: {without_contexts(m.content)}")
            try:
                contexts.extend(json.loads(m.content).get("contexts", []))
            except (json.JSONDecodeError, AttributeError):
                pass
    log = TURN_LOG.get()
    if log is not None:  # 병렬로 불려도 서브 에이전트 하나의 기록이 한 덩어리로 들어가게 한 번에 붙인다
        log["trace"].extend([name, *inner_trace])
        log["contexts"].extend(contexts)
    report = next((message_text(m.content) for m in reversed(messages)
                   if isinstance(m, AIMessage) and message_text(m.content)), "")
    return f"{report}\n\n[도구 원본 결과]\n" + "\n".join(raws)
