"""RAGAS 지표 산출: 에이전트 답(answer)과 근거(contexts)로 Faithfulness·Answer Relevancy·Context Precision 을 계산한다.

run_eval.py 가 --round 또는 --ragas 일 때만 부른다 (모델 호출이 많아 토큰을 아끼기 위해).
- Faithfulness: 답의 문장이 근거 문서에 실제로 있는 내용인가 ("지어내지 않기"를 숫자로)
- Answer Relevancy: 답이 질문에 맞는 내용인가 (임베딩: Titan v2)
- Context Precision (정답 없는 방식): 가져온 근거가 답에 쓸모 있었나
- Context Recall 은 모범 답안이 필요해 쓰지 않는다 (인-아웃 세트에 없음)
근거가 없는 답(거절·안내·질문)은 근거가 없는 것이 정답이므로 계산하지 않는다.
측정 기준: 정책상 모든 답에 붙는 안내 문구(※ 로 시작하는 줄)는 빼고 계산한다.
  이 문구가 RAGAS 에서 회피형 답으로 읽혀 답 관련성을 절반가량 깎기 때문이다 (같은 답 0.66 → 0.29~0.42).
"""

from __future__ import annotations

import asyncio
import re
import sys
import types
from os import environ

# ragas 0.4.3 은 불러올 때 langchain_community 의 VertexAI 모듈을 찾는데, 설치된 0.4.2 에는 없다.
# 우리는 VertexAI 를 쓰지 않으므로 빈 자리만 만들어 둔다.
if "langchain_community.chat_models.vertexai" not in sys.modules:
    _stub = types.ModuleType("langchain_community.chat_models.vertexai")
    _stub.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules[_stub.__name__] = _stub

from botocore.config import Config as BotoConfig  # noqa: E402
from langchain_aws import BedrockEmbeddings, ChatBedrockConverse  # noqa: E402
from ragas.embeddings.base import BaseRagasEmbedding  # noqa: E402
from ragas.llms.base import InstructorBaseRagasLLM  # noqa: E402
from ragas.metrics.collections import (  # noqa: E402
    AnswerRelevancy,
    ContextPrecisionWithoutReference,
    Faithfulness,
)

METRICS = ("faithfulness", "answer_relevancy", "context_precision")
METRIC_LABELS = {"faithfulness": "근거 충실도", "answer_relevancy": "답 관련성", "context_precision": "근거 정확도"}
DEFAULT_FALLBACKS = "us.anthropic.claude-sonnet-4-6,global.anthropic.claude-sonnet-4-5-20250929-v1:0"
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"  # 지금 AWS 키로 호출되는 유일한 임베딩 모델
CONCURRENCY = 2  # 한 번에 계산하는 문항 수 (한 문항이 지표 3개 × 여러 번 부르므로 낮게 둔다)
RETRY_ROUNDS = 4  # 모든 모델이 한도에 걸리면 기다렸다가 다시 도는 횟수
RETRY_WAIT = 15  # 첫 대기 초 (돌 때마다 늘린다)
RULE = "정책 안내 문구(※ 줄) 제외"  # 리포트와 답 저장 파일에 남기는 측정 기준
DISCLAIMER_LINE = re.compile(r"^\s*※.*$", re.MULTILINE)


def strip_disclaimer(answer: str) -> str:
    """측정 전에 정책 안내 문구 줄(※ …)을 뺀다. 답 내용은 바꾸지 않는다."""
    return DISCLAIMER_LINE.sub("", answer).strip()


def ragas_model_ids() -> list[str]:
    """RAGAS 채점 모델 순서: RAGAS_MODEL_ID(없으면 JUDGE_MODEL_ID) 다음에 예비 모델."""
    first = environ.get("RAGAS_MODEL_ID") or environ.get("JUDGE_MODEL_ID") or "global.anthropic.claude-sonnet-4-6"
    rest = environ.get("JUDGE_FALLBACK_MODEL_IDS", DEFAULT_FALLBACKS)
    return list(dict.fromkeys([first.strip(), *[m.strip() for m in rest.split(",") if m.strip()]]))


class BedrockRagasLLM(InstructorBaseRagasLLM):
    """RAGAS 가 요구하는 구조화 출력 LLM 을 Bedrock 모델로 감싼다. 한도에 걸리면 예비 모델로 넘어가고, 쓴 모델을 기록한다."""

    def __init__(self, model_ids: list[str]):
        """모델 ID 순서대로 Bedrock 모델을 만든다 (SDK 재시도는 줄여 빨리 넘어간다)."""
        self.model_ids = model_ids
        self.models = [
            ChatBedrockConverse(
                model=m,
                temperature=0,
                region_name=environ.get("AWS_DEFAULT_REGION"),
                config=BotoConfig(retries={"max_attempts": 2, "mode": "standard"}),
            )
            for m in model_ids
        ]
        self.used: set[str] = set()

    async def agenerate(self, prompt: str, response_model):
        """프롬프트를 보내 response_model(Pydantic) 형태로 받는다.

        기본 모델이 실패하면 다음 모델로 넘어가고, 모든 모델이 한도에 걸리면 잠시 기다렸다가 다시 돈다.
        """
        last_error = None
        for round_no in range(RETRY_ROUNDS):
            for model_id, model in zip(self.model_ids, self.models):
                try:
                    result = await model.with_structured_output(response_model).ainvoke(prompt)
                    self.used.add(model_id)
                    return result
                except Exception as error:  # noqa: BLE001 (한도·일시 오류면 다음 모델로 넘어간다)
                    last_error = error
            await asyncio.sleep(RETRY_WAIT * (round_no + 1))
        raise last_error

    def generate(self, prompt: str, response_model):
        """agenerate 의 동기 버전."""
        return asyncio.run(self.agenerate(prompt, response_model))


class TitanRagasEmbedding(BaseRagasEmbedding):
    """RAGAS 가 요구하는 임베딩을 Bedrock Titan v2 로 감싼다."""

    def __init__(self):
        """Titan v2 임베딩 모델을 만든다."""
        self.model = BedrockEmbeddings(model_id=EMBEDDING_MODEL_ID, region_name=environ.get("AWS_DEFAULT_REGION"))

    def embed_text(self, text: str, **kwargs) -> list[float]:
        """글 하나를 벡터로 바꾼다."""
        return self.model.embed_query(text)

    async def aembed_text(self, text: str, **kwargs) -> list[float]:
        """embed_text 의 비동기 버전. 한도에 걸리면 기다렸다가 다시 부른다."""
        for round_no in range(RETRY_ROUNDS):
            try:
                return await asyncio.to_thread(self.model.embed_query, text)
            except Exception:  # noqa: BLE001
                if round_no == RETRY_ROUNDS - 1:
                    raise
                await asyncio.sleep(RETRY_WAIT * (round_no + 1))


async def _score_one(metrics: dict, item: dict, gate: asyncio.Semaphore) -> dict:
    """문항 하나의 세 지표를 계산한다. 지표 하나가 실패해도 나머지는 남긴다."""
    async with gate:
        scores: dict = {}
        q, a, ctx = item["question"], strip_disclaimer(item["answer"]), item["contexts"]
        calls = {
            "faithfulness": lambda: metrics["faithfulness"].ascore(user_input=q, response=a, retrieved_contexts=ctx),
            "answer_relevancy": lambda: metrics["answer_relevancy"].ascore(user_input=q, response=a),
            "context_precision": lambda: metrics["context_precision"].ascore(user_input=q, response=a, retrieved_contexts=ctx),
        }
        only = item.get("only")  # 정해 주면 그 지표만 계산한다 (재계산 때 빈 값만 채우기)
        for name, call in calls.items():
            if only is not None and name not in only:
                continue
            try:
                result = await call()
                scores[name] = float(result.value)
            except Exception as error:  # noqa: BLE001
                scores[name] = None
                scores.setdefault("errors", []).append(f"{name}: {type(error).__name__}")
        return scores


async def _score_all(items: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """근거가 있는 문항들을 함께 계산하고, 문항 ID 별 점수와 실제로 쓴 채점 모델을 돌려준다."""
    llm = BedrockRagasLLM(ragas_model_ids())
    embeddings = TitanRagasEmbedding()
    metrics = {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_precision": ContextPrecisionWithoutReference(llm=llm),
    }
    gate = asyncio.Semaphore(CONCURRENCY)
    scored = await asyncio.gather(*(_score_one(metrics, item, gate) for item in items))
    return {item["id"]: s for item, s in zip(items, scored)}, sorted(llm.used)


def score_cases(items: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """items(id, question, answer, contexts)의 RAGAS 점수를 계산한다. 근거가 없는 문항은 넘긴다.

    돌려주는 값: ({문항 ID: {지표: 점수 또는 None}}, 실제로 쓴 채점 모델 목록)
    """
    targets = [i for i in items if i.get("contexts") and i.get("answer")]
    if not targets:
        return {}, []
    return asyncio.run(_score_all(targets))


def missing(scores: dict[str, dict]) -> int:
    """계산에 실패해 비어 있는 값의 개수. 0 이 아니면 평균을 그대로 믿으면 안 된다."""
    return sum(1 for s in scores.values() for m in METRICS if s.get(m) is None)


def averages(scores: dict[str, dict]) -> dict[str, float | None]:
    """지표별 평균 (계산에 실패한 값은 빼고)."""
    out = {}
    for m in METRICS:
        values = [s[m] for s in scores.values() if s.get(m) is not None]
        out[m] = sum(values) / len(values) if values else None
    return out
