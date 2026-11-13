"""공통 설정: 프로젝트 경로, 시간대, .env 읽기."""
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]  # mini-pjt/
DATA_DIR = ROOT / "data"  # 해석 문서 (RAG 근거)
STATIC_DIR = ROOT / "src" / "web" / "static"  # 웹 화면과 어진 그림 (/static 으로 제공)
EVAL_IMAGES_DIR = ROOT / "evaluation" / "images"  # 인-아웃 세트의 [사진:images/…] 표기가 가리키는 테스트 사진
KST = timezone(timedelta(hours=9))


def load_env() -> None:
    """프로젝트 루트의 .env 를 읽는다 (AWS·LangSmith·SMTP 설정). 이미 있는 환경 변수는 덮지 않는다."""
    load_dotenv(ROOT / ".env")
