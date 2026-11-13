"""LLM 클라이언트 설정: 모든 에이전트·도구가 쓰는 Bedrock 모델과 예비 모델(fallback) 순서를 한 곳에서 정한다.

모델은 코드가 아니라 .env 로 바꾼다: MODEL_ID (기본 모델), FALLBACK_MODEL_IDS (쉼표로 구분한 예비 모델).
"""
import os

from botocore.config import Config as BotoConfig
from langchain.agents.middleware import ModelFallbackMiddleware
from langchain_aws import ChatBedrockConverse

# 현재 AWS 키로 호출 가능한 이미지 입력 모델. us. 경로는 호출 한도(Throttling)에 자주 걸려,
# 같은 Sonnet 4.6 을 여러 리전에 나눠 처리하는 global. 교차 리전 경로를 쓴다
DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-4-6"
# 기본 모델이 한도(분당 몰림·하루 토큰)에 걸리면 차례로 넘어갈 예비 모델 (.env 의 FALLBACK_MODEL_IDS 로 바꿀 수 있다)
DEFAULT_FALLBACK_MODEL_IDS = "us.anthropic.claude-sonnet-4-6,global.anthropic.claude-sonnet-4-5-20250929-v1:0"


def model_ids() -> list[str]:
    """쓸 모델 ID 를 순서대로 돌려준다: 기본(MODEL_ID) 다음에 예비(FALLBACK_MODEL_IDS). 중복은 뺀다."""
    first = os.getenv("MODEL_ID", DEFAULT_MODEL_ID).strip()
    rest = [m.strip() for m in os.getenv("FALLBACK_MODEL_IDS", DEFAULT_FALLBACK_MODEL_IDS).split(",") if m.strip()]
    return list(dict.fromkeys([first, *rest]))


def bedrock_model(model_id: str) -> ChatBedrockConverse:
    """Bedrock 모델을 만든다. 한도에 걸렸을 때 같은 모델에 오래 매달리지 않고 예비 모델로 빨리 넘어가도록 SDK 재시도를 줄인다."""
    return ChatBedrockConverse(
        model=model_id,
        region_name=os.getenv("AWS_DEFAULT_REGION"),
        config=BotoConfig(retries={"max_attempts": 2, "mode": "standard"}),
    )


def chat_model() -> ChatBedrockConverse:
    """감독·서브 에이전트가 함께 쓰는 기본 Bedrock 모델을 만든다. 모델 ID 는 .env 의 MODEL_ID."""
    return bedrock_model(model_ids()[0])


def fallback_middleware() -> list:
    """기본 모델이 한도에 걸리면 예비 모델로 넘어가는 미들웨어. 예비 모델이 없으면 빈 목록."""
    rest = [bedrock_model(m) for m in model_ids()[1:]]
    return [ModelFallbackMiddleware(*rest)] if rest else []
