# 프로젝트 규칙
service.md를 보고 기획을 파악하고, history.md 보고 개발 현황을 파악해줘

## 기술 스택
- Python, LangChain
- LangGraph: 에이전트 그래프를 만들고, checkpointer 로 텍스트 대화의 이전 턴을 기억한다
- Agent 생성은 langchain.agents 의 create_agent 를 쓴다 (LangGraph 위에서 동작)
- Amazon Bedrock: 모델은 ChatBedrockConverse 로 부른다. 사진을 읽어야 하므로 이미지 입력을 지원하는 모델을 쓴다. 리전은 .env 의 AWS_DEFAULT_REGION 을 쓴다
- FastAPI: POST /query 엔드포인트를 연다
- 실행 추적은 LangSmith 로 남긴다 (.env 의 LANGSMITH_* 설정)

## 폴더 구조 (제출 규약. 제출 필수 파일 이름·위치는 바꾸지 않는다)
```
mini-pjt/
├── src/
│   ├── agent.py             메인 에이전트 그래프 (제출 필수 · 진입점 → supervisor/graph.py)
│   ├── tools.py             도메인 도구 (제출 필수 · 진입점 → 각 도메인 tools.py)
│   ├── retriever.py         RAG 파이프라인 (제출 필수 · 진입점 → knowledge/retriever.py)
│   ├── server.py            서버 실행 진입점 (uvicorn src.server:app → web/app.py)
│   ├── shared/              공통: LLM 클라이언트, 경로·설정, 메시지 유틸, 서브 에이전트 위임
│   ├── knowledge/           해석 지식 (RAG): 문서 읽기·검색·성향 유형
│   ├── face_analysis/       사진 분석: 비전 체인, analyze_face_photo, photo_agent
│   ├── reading/             풀이: 부위별 풀이·닮은 왕·닮은 동물, reading_agent
│   ├── fortune/             운세: get_fortune, fortune_agent
│   ├── supervisor/          감독 에이전트 (메인 그래프): 지시문, ask()
│   ├── guardrails/          가드레일: 입력·출력 검사, PII 가림, 미들웨어 묶음
│   ├── sharing/             E-mail 공유: SMTP 발송, 메일 문구
│   └── web/                 FastAPI 앱, API 스키마, static/ (웹 화면·어진 그림)
├── data/                    사용한 문서·데이터
├── evaluation/
│   ├── test_queries.csv     인-아웃 세트 (§4-4 스키마 필수)
│   ├── round1_report.md     1차 자체 평가 결과 (Day 9)
│   ├── round2_report.md     2차 자체 평가 결과 (Day 10, 개선 후)
│   ├── roundN_answers.json  라운드별 답·근거 저장 (RAGAS 재계산용, 사진은 넣지 않음)
│   ├── run_eval.py          평가 스크립트 (LLM-as-Judge, 라운드 리포트)
│   ├── ragas_eval.py        RAGAS 지표 산출 (근거 충실도·답 관련성·근거 정확도)
│   └── images/              테스트용 이미지 (AI 생성 얼굴 등)
├── SERVICE.md               서비스 스펙 (§4-3 템플릿 필수)
├── README.md                §4-5 템플릿 준수
├── requirements.txt
├── Dockerfile               선택
└── run.sh                   선택
```
- 제출 필수 파일(src/agent.py, src/tools.py, src/retriever.py)은 이름·위치를 바꾸지 않는다. 실제 코드는 도메인 폴더에 두고, 이 세 파일은 다시 내보내기만 한다
- src/ 의 server.py 와 도메인 폴더, evaluation/ 의 run_eval.py, ragas_eval.py, images/ 는 규약의 "..." 에 해당하는 추가 파일이다
- CLAUDE.md, history.md 는 작업용 문서다

## src/ 폴더 역할과 파일 배치 규칙
폴더는 기술 역할(utils, models)이 아니라 **에이전트의 업무 도메인**으로 나눈다. 한 도메인의 실행 로직·프롬프트·입출력 스키마는 그 도메인 폴더 안에 함께 둔다.

| 폴더 | 역할 | 파일 |
|------|------|------|
| `shared/` | 여러 도메인이 함께 쓰는 것**만** 둔다 | `llm.py` LLM 클라이언트(모델 ID·예비 모델·Bedrock 생성), `config.py` 경로·시간대·.env, `messages.py` 메시지 글 꺼내기·JSON, `delegation.py` 서브 에이전트 만들기·위임·TURN_LOG |
| `knowledge/` | 해석 문서 RAG. 풀이·운세가 함께 쓰는 지식 | `retriever.py` 읽기·검색, `traits.py` 성향 유형 고르기, `schemas.py` Chunk |
| `face_analysis/` | 사진에서 주인공 얼굴 판정과 특징 추출 | `tools.py` 비전 LCEL 체인·analyze_face_photo, `agent.py` photo_agent, `prompts.py`, `schemas.py` FaceAnalysis, `image.py` 사진 칸(CURRENT_IMAGE)·base64·형식 |
| `reading/` | 부위별 풀이·강점·약점, 닮은 조선의 왕, 닮은 동물 | `tools.py`, `agent.py` reading_agent, `prompts.py`, `schemas.py` |
| `fortune/` | 오늘·이번 주·계절 운세, 성공운 | `tools.py` get_fortune, `agent.py` fortune_agent, `prompts.py`, `schemas.py` |
| `supervisor/` | 메인 에이전트 그래프. 서브 에이전트에게 맡기고 답을 정리 | `graph.py` build_agent·ask (AGENT_MODE), `prompts.py` 단일·감독 지시문, `schemas.py` QueryResult |
| `guardrails/` | 감독 에이전트 앞뒤의 코드 검사 | `middleware.py` input_guard·output_guard·build_middleware, `rules.py` 정책 문구·패턴 |
| `sharing/` | 결과 E-mail 공유 | `mailer.py` SMTP 발송·횟수 제한, `templates.py` 제목·본문, `schemas.py` ShareRequest |
| `web/` | HTTP 와 화면 | `app.py` FastAPI 경로, `schemas.py` QueryRequest·QueryResponse, `static/` index.html·kings/ |

배치 규칙:
- 도메인 폴더의 파일 이름은 역할을 따른다: `tools.py`(LangChain 도구), `agent.py`(서브 에이전트와 위임 도구), `prompts.py`(지시문 문자열), `schemas.py`(Pydantic·TypedDict 입출력 모양). 필요할 때만 만든다
- 프롬프트 문자열은 `prompts.py` 에만 둔다. 도구·에이전트 코드 안에 지시문을 직접 쓰지 않는다
- 새 도메인 도구를 만들면: 그 도메인 `tools.py` 에 두고, 서브 에이전트에 붙이고(`agent.py`), `src/tools.py` 의 TOOLS 와 아래 "도구 이름"에 더한다
- 새 서브 에이전트를 만들면: 도메인 `agent.py` 에서 `shared.delegation` 의 build_subagent·delegate 를 쓰고, `supervisor/graph.py` 의 SUPERVISOR_TOOLS 와 감독 지시문에 더한다
- `shared/` 에는 두 도메인 이상이 쓰는 것만 둔다. 한 도메인만 쓰면 그 도메인 폴더에 둔다
- 의존 방향: `web → (supervisor·sharing)`, `supervisor → (face_analysis·reading·fortune·guardrails)`, `reading·fortune → knowledge`, 모두 `→ shared`. 이 방향으로만 import 하고, 같은 층의 도메인끼리는 서로 부르지 않는다 (여러 도메인을 묶는 것은 supervisor 와 web 뿐이다. 정책 문구는 guardrails.rules 에서 가져온다)
- import 는 `from src.도메인.파일 import 이름` 처럼 항상 src 부터 적는다
- 모델 ID 는 코드에 흩어 쓰지 않는다. `shared/llm.py` 만 정하고 .env 로 바꾼다

## 주고받는 형식 (제출 규약)
- POST /query 로 받고 question 필드를 읽는다
- 얼굴 사진은 선택 필드 image (base64 문자열)로 받는다. 사진 선택과 카메라 촬영 모두 이 필드 하나로 보낸다. 제출 규약에 없는 추가 필드다
- image 가 없으면 텍스트 대화 모드로 처리한다. 여러 턴 대화를 이어 가도록 선택 필드 session_id 를 받는다 (LangGraph checkpointer 의 thread_id 로 쓴다). 제출 규약에 없는 추가 필드다
- 답은 answer, contexts, trace 세 키로 돌려준다

## 사진 처리
- 사진은 요청을 처리하는 동안 메모리에서만 다룬다. 파일·DB·로그에 남기지 않는다
- LangSmith trace 에도 image 원본을 넣지 않는다
- 카메라 촬영은 브라우저 getUserMedia 로 한다. HTTPS 나 localhost 에서만 동작한다
- 카메라 권한 거부나 카메라 없음 같은 오류가 나면 화면이 텍스트 대화 모드로 넘어간다
- E-mail 공유로 보내는 결과에는 얼굴 사진을 넣지 않는다 (받는 쪽 메일 서버에 남기 때문). 받는 주소·내용은 저장하거나 로그에 남기지 않는다

## 인-아웃 세트 (§4-4 스키마)
- 열: id(1부터), category(positive/negative/edge/guardrail), input, expected_traits(필수) / forbidden, expected_tools, note(선택). 목록 칸은 세미콜론으로 구분
- 카테고리 비율: positive 40%, negative 20%, edge 25%, guardrail 15%. 지금 20건 = 8 / 4 / 5 / 3
- 사진 문항은 input 앞에 [사진:images/파일명] 을 붙인다. 평가 스크립트가 떼어 내어 image 필드로 보낸다
  - 채점 쪽이 input 을 그대로 question 에 보내도 되도록, 서버(supervisor.graph.ask)는 image 필드가 비어 있으면 이 표기를 읽어 evaluation/images/ 의 사진을 쓴다 (face_analysis.image.image_from_notation)
  - 이 폴더 안의 이미지 파일(jpg·png·webp·gif, 10MB 이하)만 읽는다. 폴더 밖 경로와 다른 파일은 거부하고 "사진 없음"으로 처리한다
- 문항은 한 번의 요청으로 끝난다. 여러 턴 대화는 session_id 로 앱에서 지원하되 세트에는 넣지 않는다

## 도구 이름 (expected_tools 와 trace 에 쓰는 이름. 바꾸면 세트도 같이 고친다)
- analyze_face_photo: 사진에서 얼굴을 찾고 이마·눈·코·입·귀 특징을 뽑는다 (얼굴 없음·여러 명·어두움 판정 포함)
- search_reading_docs: data/ 해석 문서에서 특징에 맞는 풀이를 찾는다 (RAG)
- find_similar_animals: 특징으로 육지·해상·공중 닮은 동물과 이유를 찾는다
- find_similar_king: 특징으로 관상 유형(성향)이 닮은 조선의 왕과 업적·닮은 점·어진 그림 경로를 찾는다 (외모가 닮았다고 하지 않는다)
- get_fortune: 날짜와 특징으로 오늘·이번 주·계절 운세와 성공운을 만든다
- trace 에는 호출한 도구 이름을 순서대로 담는다
- 에이전트 구성은 Multi-Agent Supervisor 다. 감독 에이전트가 서브 에이전트(photo_agent, reading_agent, fortune_agent)에게 맡기고,
  trace 에는 서브 에이전트 이름 뒤에 그 안에서 부른 도구 이름이 이어진다 (예: photo_agent, analyze_face_photo, reading_agent, …)
- .env 의 AGENT_MODE=single 이면 단일 에이전트가 도구를 직접 부른다 (되돌리기용)

## 평가 루프 (고치고 다시 재는 순환)
- 잣대는 evaluation/test_queries.csv 하나다. 점수를 올리려고 문항이나 기대 동작을 고치지 않는다. 문항을 바꿔야 하면 사람에게 먼저 묻는다
- 한 바퀴:
  1. 서버를 띄우고 python evaluation/run_eval.py --note "고친 내용" 을 돌린다
  2. evaluation/latest_report.md 에서 실패 문항과 이유를 읽는다
  3. 실패 원인 하나를 골라 그 원인만 고친다 (프롬프트, 도구, 해석 문서 중 하나)
  4. 실패했던 문항만 --only 9,18 처럼 먼저 돌려 보고, 그다음 전체를 다시 돌린다
  5. evaluation/runs.csv 의 직전 점수와 비교한다. 점수가 떨어졌거나 전에 통과하던 문항이 실패하면 그 변경을 되돌린다
- 20건 중 17건 이상이면서 guardrail·negative 카테고리 문항이 모두 통과하면 멈춘다
- 같은 문항이 세 바퀴 연속 실패하면 멈추고 사람에게 보고한다
- 제출용 리포트는 사람이 정한 시점에만 남긴다: Day 9 에 --round 1 (round1_report.md), 개선 후 Day 10 에 --round 2 (round2_report.md). 루프 중간에는 --round 를 쓰지 않는다
- 지표는 두 가지다: LLM-as-Judge 통과 수(목표 판정)와 RAGAS 평균(근거 충실도·답 관련성·근거 정확도, 근거가 있는 문항만)
  - RAGAS 는 모델 호출이 많아 --round 일 때만 계산한다. 루프 중간에 RAGAS 를 보려면 --ragas 를 붙인다 (하루 토큰 한도 주의)
  - 2차 리포트는 runs.csv 의 1차 기록과 비교 표를 넣는다
  - RAGAS 측정 기준: 정책 안내 문구(※ 줄)는 빼고 잰다. 기준을 바꾸면 --rescore N 으로 저장된 roundN_answers.json 을 같은 기준으로 다시 계산해 비교한다
- 한 바퀴가 끝날 때마다 history.md 작업 기록에 점수와 고친 내용을 적는다

## 코드 규칙
- 파일 하나에 한 가지 역할만 둔다
- 함수와 도구에는 한국어 docstring 을 쓴다
- 비밀 값은 .env 에서 읽고 코드에 적지 않는다. .env 는 커밋하지 않는다

## 하지 말 것
- 요청하지 않은 파일을 새로 만들지 않는다
- 기존 파일을 통째로 다시 쓰지 않는다. 바뀐 부분만 고친다
