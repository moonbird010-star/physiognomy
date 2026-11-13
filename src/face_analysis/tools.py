"""사진 분석 도구: LCEL 비전 체인과 analyze_face_photo."""
import base64
from functools import lru_cache

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langsmith import tracing_context

from src.face_analysis.image import CURRENT_IMAGE, mime_of
from src.face_analysis.prompts import VISION_PROMPT
from src.face_analysis.schemas import FaceAnalysis
from src.shared.llm import bedrock_model, model_ids
from src.shared.messages import to_json


def _vision_messages(photo: dict) -> list:
    """사진 바이트와 형식으로 비전 모델에 보낼 메시지를 만든다."""
    image = {"type": "image", "source_type": "base64", "data": base64.b64encode(photo["data"]).decode(), "mime_type": photo["mime"]}
    return [HumanMessage(content=[{"type": "text", "text": VISION_PROMPT}, image])]


@lru_cache(maxsize=1)
def vision_chain():
    """LCEL 체인: 메시지 만들기 | 비전 모델 → FaceAnalysis(Pydantic) 구조화 출력. 기본 모델이 실패하면 예비 모델로 넘어간다."""
    structured = [bedrock_model(m).with_structured_output(FaceAnalysis) for m in model_ids()]
    return RunnableLambda(_vision_messages) | structured[0].with_fallbacks(structured[1:])


@tool
def analyze_face_photo() -> str:
    """사용자가 첨부한 얼굴 사진을 분석한다. 인자는 없다 (사진은 서버가 넘겨준다).

    얼굴이 없거나(status=no_face), 여러 명이거나(multiple_faces), 어둡거나 흐리면(poor_quality)
    풀이하지 말고 안내만 한다. status=ok 이면 features 에 이마·눈·코·입·귀 특징이 담긴다.
    """
    data = CURRENT_IMAGE.get()
    if not data:
        return to_json({"status": "no_image", "message": "첨부된 사진이 없다."})
    mime = mime_of(data)
    if mime is None:
        return to_json({"status": "unsupported_format", "message": "JPG·PNG·WEBP·GIF 사진만 볼 수 있다."})
    # 사진 원본이 LangSmith 에 남지 않도록 이 호출만 추적을 끈다.
    with tracing_context(enabled=False):
        result: FaceAnalysis = vision_chain().invoke({"data": data, "mime": mime})
    if result.main_subject == "none" or result.human_face_count == 0:
        return to_json({"status": "no_face", "message": "사진에서 사람 얼굴을 찾지 못했다."})
    if result.main_subject == "several_similar_faces":
        return to_json({"status": "multiple_faces", "message": "비슷한 크기의 얼굴이 여러 개라 누구를 볼지 정할 수 없다."})
    if result.quality != "good":
        return to_json({"status": "poor_quality", "message": "사진이 어둡거나 흐려 생김새를 판단하기 어렵다."})
    features = {
        "이마": result.forehead,
        "눈": result.eyes,
        "코": result.nose,
        "입": result.mouth,
        "귀": result.ears,
    }
    result_data = {"status": "ok", "features": features}
    if result.human_face_count > 1:
        result_data["note"] = "뒤쪽에 다른 사람이 찍혀 있어 가장 앞의 주인공 얼굴만 풀이한다. 다른 사람은 언급하지 않는다."
    return to_json(result_data)
