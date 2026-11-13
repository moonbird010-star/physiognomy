"""서버 실행 진입점: uvicorn src.server:app --port 8000

실제 FastAPI 앱은 웹 도메인 src/web/app.py 에 있다 (uvicorn src.web.app:app 으로도 띄울 수 있다).
"""
from src.web.app import app  # noqa: F401
