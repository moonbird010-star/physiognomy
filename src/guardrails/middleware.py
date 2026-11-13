"""가드레일 미들웨어: 입력 검사(before_agent), 출력 검사(after_model), PII 가림·요약·재시도를 묶어 에이전트에 붙인다."""
import re

from langchain.agents.middleware import (
    AgentState,
    ModelRetryMiddleware,
    PIIMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
    after_model,
    before_agent,
)
from langchain_core.messages import AIMessage, HumanMessage

from src.guardrails.rules import (
    ASSERTIVE,
    BLOCKED_ANSWER,
    BUSY_ANSWER,
    DISCLAIMER,
    DISCLAIMER_EN,
    FORBIDDEN_JUDGMENT,
    INJECTION,
    INJECTION_NOTE,
    KR_PHONE,
    KR_RRN,
    MODEL_FAILURE,
    PROBABILITY,
    REFUSING,
    SENSITIVE,
    SENSITIVE_NOTE,
)
from src.shared.messages import message_text


@before_agent
def input_guard(state: AgentState, runtime) -> dict | None:
    """사용자 입력에서 지시 무시 요청과 판단 금지 주제를 찾아, 따르지 말라는 표시를 붙인다."""
    messages = state["messages"]
    last = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if last is None:
        return None
    text = message_text(last.content)
    notes = []
    if INJECTION.search(text):
        notes.append(INJECTION_NOTE)
    if SENSITIVE.search(text):
        notes.append(SENSITIVE_NOTE)
    if not notes or "[입력 검사]" in text:
        return None
    marked = f"{text}\n\n[입력 검사] " + " ".join(notes)
    return {"messages": [HumanMessage(content=marked, id=last.id)]}  # 같은 id 로 바꿔 끼운다


@after_model
def output_guard(state: AgentState, runtime) -> dict | None:
    """최종 답을 검사한다. 금지된 판단은 막고, 풀이 속 단정 표현은 누그러뜨리고, 재미 안내를 붙인다."""
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or last.tool_calls:
        return None  # 도구를 부르는 중간 단계는 건드리지 않는다
    text = message_text(last.content)
    fixed = text
    if MODEL_FAILURE.search(fixed) and "## " not in fixed:
        fixed = BUSY_ANSWER  # 모델 오류 원문(영어)을 사용자에게 그대로 보이지 않는다
    elif FORBIDDEN_JUDGMENT.search(fixed) and ("## " in fixed or not REFUSING.search(fixed)):
        fixed = BLOCKED_ANSWER  # 풀이나 단정 속에 금지된 판단이 있으면 답 전체를 막는다 (거절 문장은 그대로 둔다)
    else:
        if "## " in fixed:  # 풀이 답에만 적용한다 (거절·안내 문장의 "확실히" 등은 그대로 둔다)
            for word, soft in ASSERTIVE:
                fixed = fixed.replace(word, soft)
            fixed = PROBABILITY.sub("", fixed)
        if "※" not in fixed:
            english = not re.search(r"[가-힣]", fixed)
            fixed = f"{fixed.rstrip()}\n\n{DISCLAIMER_EN if english else DISCLAIMER}"
    if fixed == text:
        return None
    return {"messages": [AIMessage(content=fixed, id=last.id)]}


def build_middleware(summary_model, fallback: list | None = None) -> list:
    """에이전트에 붙일 미들웨어 목록을 만든다. 순서대로 입력 → 모델 → 출력에 걸린다.

    fallback 은 예비 모델 미들웨어 목록이다. 재시도 안쪽에 두어, 기본 모델이 한도에 걸리면 바로 예비 모델로 넘어간다.
    """
    return [
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("kr_phone", detector=KR_PHONE, strategy="redact"),
        PIIMiddleware("kr_rrn", detector=KR_RRN, strategy="redact"),
        input_guard,
        SummarizationMiddleware(model=summary_model, trigger=("tokens", 6000), keep=("messages", 12)),
        ModelRetryMiddleware(max_retries=2, initial_delay=2.0),
        *(fallback or []),
        ToolRetryMiddleware(max_retries=1, initial_delay=2.0),
        output_guard,
    ]
