"""FastAPI 앱: POST /query, POST /share-email 과 웹 화면(GET /, /static)을 제공한다."""
from src.shared.config import STATIC_DIR, load_env

load_env()  # LangSmith·AWS·SMTP 설정을 에이전트보다 먼저 읽는다

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from src.sharing import mailer  # noqa: E402
from src.sharing.schemas import ShareRequest  # noqa: E402
from src.supervisor.graph import ask  # noqa: E402
from src.web.schemas import QueryRequest, QueryResponse  # noqa: E402

INDEX = STATIC_DIR / "index.html"

app = FastAPI(title="내가 왕이 될 상인가? · 재미로 보는 관상")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")  # 어진 그림 등 화면 파일


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> dict:
    """질문과 선택 사진을 받아 관상 풀이를 돌려준다. 사진은 저장하지 않는다."""
    return ask(req.question, req.image, req.session_id)


@app.post("/share-email")
def share_email(req: ShareRequest, request: Request) -> dict:
    """관상 결과를 입력한 이메일 주소로 보낸다. 주소·내용은 저장하거나 로그에 남기지 않는다."""
    client = request.client.host if request.client else "unknown"
    try:
        mailer.send_result(req.email, req.html, req.summary, client)
    except mailer.MailError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"ok": True, "message": "메일을 보냈어요. 받은편지함(또는 스팸함)을 확인해 주세요."}


@app.get("/", response_class=HTMLResponse)
def index():
    """웹 화면을 돌려준다. 아직 화면 파일이 없으면 API 문서로 안내한다."""
    if INDEX.exists():
        return FileResponse(INDEX)
    return HTMLResponse('<p>웹 화면 준비 중입니다. <a href="/docs">/docs</a> 에서 POST /query 를 시험할 수 있습니다.</p>')
