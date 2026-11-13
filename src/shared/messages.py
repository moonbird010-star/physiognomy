"""메시지 유틸리티: LangChain 메시지에서 글 꺼내기, 도구 결과를 JSON 으로 만들기."""
import json


def message_text(content) -> str:
    """메시지 내용(문자열 또는 블록 목록)에서 글만 꺼낸다."""
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict))


def to_json(data: dict) -> str:
    """도구 결과를 한글이 보이는 JSON 문자열로 만든다."""
    return json.dumps(data, ensure_ascii=False)
