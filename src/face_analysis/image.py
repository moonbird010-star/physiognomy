"""사진 다루기: 요청 동안만 사진을 들고 있는 칸, base64 풀기, 형식 알아내기. 사진은 파일·DB·로그에 남기지 않는다."""
import base64
import binascii
import re
from contextvars import ContextVar

from src.shared.config import EVAL_IMAGES_DIR

# 인-아웃 세트 표기: input 앞의 [사진:images/파일명] (채점 쪽이 input 을 question 에 그대로 보낼 때를 대비한다)
PHOTO_NOTATION = re.compile(r"^\s*\[사진:\s*([^\]]+?)\s*\]\s*")
NOTATION_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
NOTATION_MAX_BYTES = 10_000_000

# 요청을 처리하는 동안에만 사진 바이트를 들고 있는 칸. 메시지·checkpointer·로그에 넣지 않는다.
CURRENT_IMAGE: ContextVar[bytes | None] = ContextVar("CURRENT_IMAGE", default=None)


def decode_image(image_b64: str | None) -> bytes | None:
    """base64 사진 문자열을 바이트로 바꾼다. data URL 머리말은 떼어 낸다."""
    if not image_b64:
        return None
    if image_b64.startswith("data:"):
        image_b64 = image_b64.split(",", 1)[-1]
    try:
        return base64.b64decode(image_b64, validate=False)
    except (binascii.Error, ValueError):
        return b""


def image_from_notation(question: str) -> tuple[str, bytes | None]:
    """question 앞의 [사진:images/파일명] 표기를 떼고, evaluation/images/ 의 그 사진을 읽어 돌려준다.

    표기가 없으면 (question 그대로, None). 표기가 있으면 (표기를 뗀 질문, 사진 바이트).
    파일을 찾지 못했거나 허용되지 않는 경로면 사진 바이트는 b"" 다 (사진 분석이 '사진 없음'으로 안내한다).
    보안: evaluation/images/ 폴더 안의 이미지 파일만 읽는다. 폴더 밖 경로(../ 등)와 다른 종류의 파일은 거부한다.
    """
    match = PHOTO_NOTATION.match(question or "")
    if not match:
        return question, None
    rest = question[match.end():]
    name = match.group(1).replace("\\", "/").removeprefix("images/")
    base = EVAL_IMAGES_DIR.resolve()
    path = (base / name).resolve()
    if path.parent != base or path.suffix.lower() not in NOTATION_EXTS or not path.is_file():
        return rest, b""
    if path.stat().st_size > NOTATION_MAX_BYTES:
        return rest, b""
    return rest, path.read_bytes()


def mime_of(data: bytes) -> str | None:
    """사진 바이트 앞부분으로 형식을 알아낸다. Bedrock 이 받는 형식이 아니면 None."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:3] == b"GIF":
        return "image/gif"
    return None
