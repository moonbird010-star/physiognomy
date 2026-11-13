# HISTORY · 재미로 보는 관상 웹앱 Agent

개발 현황 기록. 기획은 SERVICE.md, 규칙은 CLAUDE.md 를 본다.
작업이 끝날 때마다 "현재 상태"와 "작업 기록"을 고친다.

## 현재 상태 (2026-11-11 기준)
- 단계: 기획 문서와 평가 준비. 에이전트 코드는 아직 없다
- 제출 폴더 구조는 CLAUDE.md "폴더 구조"를 따른다

| 영역 | 파일 | 제출 | 상태 |
|------|------|------|------|
| 서비스 스펙 | SERVICE.md | 필수 (§4-3 템플릿) | 초안 완료. 템플릿 대조 필요 |
| 메인 에이전트 그래프 | src/agent.py | 필수 | 완료. create_agent + InMemorySaver, 시스템 프롬프트에 가드레일 |
| 도메인 도구 | src/tools.py | 필수 | 완료. 도구 4개 |
| RAG 파이프라인 | src/retriever.py | 필수 | 완료 (키워드·글자 묶음 검색, 점수 0.3 미만은 버림) |
| API 서버 | src/server.py | 추가 | 완료. POST /query, GET / (화면 파일 없으면 /docs 안내). uvicorn src.server:app --port 8000 |
| 웹 화면 | src/web/static/index.html | 추가 | B안 연결 완료 (POST /query, session_id, 사진 선택·촬영, 카메라 실패 시 텍스트 전환). 브라우저 수동 확인 필요 |
| 해석 문서 (더미) | data/ | 필수 | 4개 작성 완료: face_parts(부위 17), traits(유형 7), fortune(운세), animals(육지·해상·공중 각 5) |
| 인-아웃 세트 | evaluation/test_queries.csv | 필수 (§4-4 스키마) | 20건, §4-4 스키마로 재작성 완료 |
| 1차 자체 평가 | evaluation/round1_report.md | 필수 (Day 9) | 시작 전 |
| 2차 자체 평가 | evaluation/round2_report.md | 필수 (Day 10) | 시작 전 |
| 평가 스크립트 | evaluation/run_eval.py | 추가 | 완료. --round 1/2 로 제출 리포트 생성 |
| 테스트 이미지 | evaluation/images/ | 추가 | 9장 준비 완료. dark_face·two_people 은 받은 사진을 가공, cat·landscape 는 코드로 그린 그림 |
| 실행 안내 | README.md | 필수 (§4-5 템플릿) | 초안 완료 (사용자가 준 템플릿 기준). 2차 라운드 뒤 통과율·RAGAS 숫자 갱신 필요 |
| 의존성 | requirements.txt | 필수 | 완료 |
| 클린 환경·실행 | Dockerfile, run.sh | 선택 | 미정 |
| 작업용 문서 | CLAUDE.md, history.md | - | 작성 중 |

## 정해진 것
- 서비스: 일반 사용자 대상, 재미로 보는 관상
- 입력: 사진 선택 → 카메라 촬영 → 둘 다 안 되면 텍스트 대화
- 텍스트 대화: 이마·눈·코·입·귀 순서로 묻고 사진과 같은 형식으로 풀이
- 데이터: 부위별 관상 해석 문서를 직접 작성한 더미로 만든다
- 스택: Python, LangChain, LangGraph, Bedrock(ChatBedrockConverse), FastAPI, LangSmith
- API: POST /query 로 question 을 받고 answer, contexts, trace 를 돌려준다
  - 추가 필드 image(base64): 사진 선택·촬영 공용
  - 추가 필드 session_id: 텍스트 대화를 이어 가는 데 쓴다 (checkpointer thread_id)
- 사진은 메모리에서만 다루고 파일·DB·로그·LangSmith 에 남기지 않는다

## 열린 질문
- [ ] image, session_id 추가 필드가 제출 규약상 허용되는지 강사 확인
- [x] 웹 화면 위치: src/static/index.html, FastAPI 는 src/server.py (제출 구조의 src/... 에 해당)
- [x] §4-4 인-아웃 세트 스키마 반영 (20건, 사진은 input 앞 [사진:경로] 표기)
- [ ] 사진 문항의 [사진:경로] 표기가 §4-4 채점 방식과 맞는지 강사 확인
- [ ] §4-3 SERVICE.md 템플릿, §4-5 README.md 템플릿 원문 확인
- [x] 화면 시안: B안 채팅형 + 백자 청화 스타일로 결정. 배경은 조선 왕족 차림(익선관·곤룡포) 창작 인물 일러스트
  - 영화 〈관상〉 수양대군 이미지는 저작권·배우 초상 문제로 쓰지 않는다
- [x] 지난 운세 기록: 필요 없음. 운세는 날짜로 그때그때 계산하고 저장하지 않는다
- [x] answer, contexts, trace 자료형: answer 문자열, contexts 근거 섹션 문자열 목록("[파일 · 제목]\n본문"), trace 호출한 도구 이름 목록
- [x] 모델: global.anthropic.claude-sonnet-4-6 (같은 Sonnet 4.6, 교차 리전 경로). us. 경로는 Throttling 이 잦아 바꿈. Sonnet 5/5.5·Haiku 5.5·Opus 는 권한 없음. 예비: global Sonnet 4.5, Haiku 4.5, Nova Pro (.env MODEL_ID 로 바꿀 수 있음)
- [ ] 사내 기여·규모 수치(SERVICE.md 2번)가 실제 의도와 맞는지
- [ ] Bedrock 하루 토큰 한도: global Sonnet 4.6 이 "Too many tokens per day" 에 걸림 (평가를 여러 번 돌려 소진). 모델 대체(fallback)로 서비스는 계속 되지만 느려짐
- [x] LLM 채점 모델: .env 에 JUDGE_MODEL_ID=global.anthropic.claude-sonnet-4-6 추가. 이제 명령에 따로 붙이지 않아도 run_eval.py 가 읽는다

## 다음 할 일
1. 열린 질문 정리
2. ~~data/ 에 부위별 관상 해석 더미 문서 작성~~ (완료)
3. ~~evaluation/images/ 에 테스트 이미지 9장 준비~~ (완료)
4. src/retriever.py → src/tools.py → src/agent.py → src/server.py 순서로 구현, requirements.txt 작성
5. ~~POST /query 를 연 뒤 평가 루프 시작~~ (4바퀴 만에 20/20, 목표 달성)
6. Day 9: run_eval.py --round 1 로 round1_report.md
7. 개선 후 Day 10: run_eval.py --round 2 로 round2_report.md
8. 웹 화면(src/static/index.html) 연결, README.md 작성

## 작업 기록
### 2026-11-11
- 개발 환경: Ouroboros 플러그인 설정 (uv 설치, Claude 런타임 지정)
- SERVICE.md 작성: 회의실 안내 예시에서 관상 서비스로 변경
- 입력 방식 확정: 사진 선택, 카메라 촬영, 텍스트 대화(대체 수단)
- CLAUDE.md 작성: 스택, 폴더 구조, 주고받는 형식, 사진 처리 규칙
- history.md 작성
- 인-아웃 세트 12건 작성: 사진 7(정상 4, 얼굴 아님 2, 두 사람 1), 텍스트 대화 5. 금지 주제 P04·T03·T04
- 평가 스크립트 작성, CLAUDE.md 에 평가 루프 규칙 추가. 서버가 없어 실제 점수는 아직 없음
- 결과 구성 확장: 강점·약점·성장 방향, 성격·재능·잠재력, 오늘·주간·계절 운세, 성공운 (SERVICE.md 1-2)
- 단일 HTML 모의 화면 3안 작성. 상단 문구 "내가 왕이 될 상인가? AI로 풀어보는 나의 운명 이야기", 배경은 가상 여성 모델 일러스트
- 흐름·스타일을 나눈 단일 HTML 목업 3개(A 궁궐, B 백자, C 네온) 작성 후 B안으로 결정. 배경은 조선 왕족 차림 창작 인물로 교체
- 결과에 닮은 동물(육지·해상·공중) 추가
- 제출 폴더 구조 반영: CLAUDE.md 폴더 구조 갱신, run_eval.py 에 --round 1/2 추가 (round1·2_report.md 생성)
- Seed 작성 (~/.ouroboros/seeds/gwansang-agent.seed.yaml, MCP 미연결로 직접 작성)
- 인-아웃 세트를 §4-4 스키마로 다시 작성: 20건(positive 8, negative 4, edge 5, guardrail 3). 목표 17/20 + guardrail·negative 전부 통과
- 도구 이름 확정: analyze_face_photo, search_reading_docs, find_similar_animals, get_fortune (CLAUDE.md)
- data/ 해석 더미 문서 4개 작성. "## 부위 · 특징" 한 섹션에 한 특징 (RAG 청크 단위). 점·주름·눈썹 등은 일부러 넣지 않음 (12번 negative 문항용). 닮은 동물에 비하로 들릴 동물은 넣지 않음
- 에이전트·서버 구현: retriever.py, tools.py, agent.py, server.py, requirements.txt 작성, fastapi 설치, 로컬 서버(8000) 실행
  - 검색: 키워드 방식 (임베딩 모델 안 씀)
  - 사진 처리: 사진은 에이전트 메시지·checkpointer 에 넣지 않고 contextvar 로 analyze_face_photo 에만 넘긴다. 그 안의 비전 호출은 LangSmith tracing_context(enabled=False)
  - 모델: Sonnet 5.5 는 AccessDenied 라 us.anthropic.claude-sonnet-4-6 으로 변경
  - 수동 확인 3건 통과: 닮은 동물 텍스트(7번), face_01 전체 풀이(1번, 도구 4개 호출·contexts 14개), 고양이 사진(9번, 풀이 없이 안내)
- 웹 화면 연결: src/static/index.html (B안 스타일 유지, 외부 스크립트 없이 마크다운 렌더링, 근거 문서 접기 목록)
  - 사진은 브라우저에서 최대 1024px JPEG 로 바꿔 보낸다 (AVIF 등 형식 문제 해결)
  - 카메라는 버튼을 누를 때만 켜고, 실패하면 "카메라가 안 켜져요…"를 보내 텍스트 대화로 넘어간다
- 평가 1바퀴 (첫 전체 실행, 채점 모델 us.anthropic.claude-sonnet-4-6): **14/20**. positive 7/8, negative 1/4, edge 4/5, guardrail 2/3
  - 실패: 6·12·17 search_reading_docs 미호출, 9·10 채점이 "이마, 눈, 코…" 안내 문구를 forbidden "이마는"으로 판정, 17 영어 질문에 풀이 대신 추가 질문, 19 신원 추측 거절 안내 없이 바로 풀이
- 웹 화면을 목업 B안대로 수정
  - 카메라 시트가 처음부터 보이던 문제 수정 (.sheet 의 display 가 hidden 속성을 덮어씀)
  - 전체 풀이는 대화창에 요약 카드 + "전체 결과 보기" 시트 (相 낙관, 바로가기, 닮은 동물 카드, 강점·약점 2단, 성장 방향, 운세, 부위별 풀이와 근거)
  - 패널 폭 390px, 높이 740px 로 목업과 맞춤
  - 화면이 섹션을 읽을 수 있도록 agent.py 시스템 프롬프트에 답 형식(## 제목과 줄 형식) 고정. 평가 점수에 영향이 있을 수 있어 다음 바퀴에서 다시 잰다
  - 배경 일러스트 부위 글자(이마·눈·코·입)가 화면 밖으로 잘리던 문제 수정 (left:-40px → 0, 글자에 바탕색 테두리). 대화창 머리의 .grow 클래스 충돌로 생긴 회색 상자 제거. Edge headless 스크린샷으로 확인
- 채점 지침 보완 (사람 결정): forbidden 은 실제 풀이·판단으로 말했을 때만 위반, 질문·안내 속 부위 이름은 위반 아님. test_queries.csv 는 그대로
- 평가 2바퀴 (답 형식 고정 + 채점 지침 보완): **15/20**. positive 6/8, negative 3/4, edge 4/5, guardrail 2/3. 9·10 통과로 바뀜
  - 실패: 6·8·12·17 공통 원인 = 특징을 일부만 말하면 search_reading_docs 없이 나머지 부위를 더 물음. 19 = 신원 추측 거절 안내 없이 풀이
- 평가 3바퀴 수정: agent.py 입력 흐름 규칙 "구체적인 생김새를 하나라도 말했으면 더 묻지 말고 search_reading_docs 로 바로 답" (영어·자료에 없는 특징 포함)
  - 실패 문항만 먼저: --only 6,8,12,17 → 4/4 통과
- 평가 3바퀴 결과: **19/20** (positive 8/8, negative 4/4, edge 5/5, guardrail 2/3). 남은 실패 19 = 사진이 있으면 무조건 분석부터 해서 신원 질문에도 풀이함
- 평가 4바퀴 수정: agent.py 입력 흐름 맨 앞에 "사진 속 인물 신원을 묻거나 남(연예인 등)의 사진이면 도구 없이 거절, 신원 추측 안 한다고 말하고 본인 사진 안내"
  - --only 19 → 통과. 전체 → **20/20** (positive 8/8, negative 4/4, edge 5/5, guardrail 3/3). 목표 달성으로 루프 멈춤
- 웹 화면 안내 문구 선명도 개선 (배경 투명도 0.4, 글자 진하게·번짐 테두리)
- 카메라 촬영 인식 개선: 교실에서 찍은 웹캠 사진(다운로드.jpeg, 다운로드2.jpeg)이 배경 사람까지 세어 "여러 명"(2명, 10명)으로 거절되던 문제
  - tools.py FaceAnalysis 에 main_subject(one_main_face / several_similar_faces / none) 추가. 주인공 얼굴이 분명하면 배경 얼굴은 무시하고 풀이, 비슷한 크기 얼굴이 여럿일 때만 거절
  - 확인: 두 웹캠 사진 ok, two_people 여전히 거절, cat·landscape no_face, dark_face poor_quality. 전체 평가 **20/20** 유지
- 결과에 "나와 닮은 조선의 왕" 추가 (사용자 요청)
  - 얼굴이 아니라 관상 유형(성향)으로 고른다: 기획가→정조, 소통가→영조, 개척자→태조, 조력자→문종, 장인→성종, 살림꾼→숙종, 창작가→세종 (data/kings.md)
  - 도구 find_similar_king 추가 (CLAUDE.md 도구 이름에 반영). 전체 풀이는 도구 5개 호출
  - 어진 그림: 원본이 남은 태조·영조만 Wikimedia Commons 퍼블릭 도메인 파일로 src/static/kings/ 에 저장. 나머지 왕은 "남아 있는 어진이 없어요" 표시. 현대 표준영정은 저작권 때문에 쓰지 않음
  - server.py 에 /static 마운트, 화면에 왕 카드(어진·유형·업적·닮은 점)와 요약 카드 "닮은 조선의 왕" 추가
  - 전체 평가 **20/20** 유지
- 빌드 체크리스트(Day 1~7 패턴 12개) 대조: 확실히 적용 4개(#2 ReAct, #4 도구 다중, #11 LangSmith, #12 LLM-as-Judge) + 일부 3개(#1, #3, #6)
- 체크리스트 보강 (사용자 요청, 확실히 적용 7개로)
  - #1 LCEL: tools.py 사진 분석을 vision_chain() = RunnableLambda(메시지) | 모델.with_structured_output(FaceAnalysis) 로 변경
  - #8 미들웨어 + #6 코드 가드레일: src/guardrails.py 새로 만듦 (CLAUDE.md 폴더 구조 반영)
    - PIIMiddleware: 이메일·휴대폰·주민번호 가림 → 대화 메모리에 [REDACTED_…] 로만 남는 것 확인
    - input_guard(before_agent): 인젝션·판단 금지 주제 감지 시 [입력 검사] 표시
    - output_guard(after_model): 풀이 속 금지 판단이면 답 차단(거절 문장은 그대로), 단정 표현 누그러뜨림, 재미 안내 보장
    - SummarizationMiddleware(6000토큰 넘으면 요약), ModelRetry·ToolRetry(Bedrock Throttling 대비)
  - 평가: 19/20 (9번 실패) → 9번만 두 번 다시 돌려 모두 통과. 출력 검사가 건드리지 않는 답이라 LLM 변동으로 판단, 되돌리지 않음
- 체크리스트 보강 + 왕 25명 반영 후 전체 재측정: **20/20** (positive 8/8, negative 4/4, edge 5/5, guardrail 3/3)
- Multi-Agent Supervisor 전환 (사용자 요청, 체크리스트 #9)
  - src/subagents.py 새로 만듦: photo_agent(analyze_face_photo), reading_agent(search_reading_docs·find_similar_king·find_similar_animals), fortune_agent(get_fortune)를 각각 create_agent 로 만들고 도구로 감쌈
  - 감독 에이전트(agent.py)는 서브 에이전트에게 맡기고 보고를 모아 답한다. 가드레일·미들웨어·checkpointer 는 감독에만. 감독 지시문은 단일 지시문에서 도구 이름 부분만 바꿔 만든다 (못 바꾸면 시작 때 오류)
  - 서브 에이전트 안쪽 도구 호출·근거는 TURN_LOG(contextvar)로 모아 trace·contexts 에 담는다
  - AGENT_MODE=single 로 예전 단일 에이전트로 되돌릴 수 있다
  - 확인: 전체 풀이는 photo → reading·fortune 병렬, 약 44초. 고양이 12초, 닮은 동물 11.5초
  - 평가: 19/20 (6번: 운세가 말한 특징과 연결 안 됨) → 운세 담당 보고에 특징별 문구와 출처 특징을 넣도록 수정 → --only 6 통과 → 전체 **20/20**
- 모델 한도 대응
  - us. Sonnet 4.6 이 분당 Throttling → 기본 모델을 global.anthropic.claude-sonnet-4-6 으로 변경
  - 이후 평가 중 global Sonnet 4.6 이 하루 토큰 한도 도달 (1~10번 통과 후 11번 채점에서 중단, runs.csv 기록 없음)
  - 모델 대체 추가: 순서 global Sonnet 4.6 → us Sonnet 4.6 → global Sonnet 4.5 (.env FALLBACK_MODEL_IDS 로 변경 가능)
    - 에이전트: ModelFallbackMiddleware (감독·서브 모두), 사진 분석 LCEL 체인: with_fallbacks, 채점: with_fallbacks (JUDGE_FALLBACK_MODEL_IDS)
    - SDK 재시도를 4→2 로 줄여 빨리 넘어가게 함 (tools.bedrock_model)
  - 확인: 기본 모델이 막힌 상태에서 전체 풀이 75초(평소 44초), 닮은 동물 38초, 500 오류 0건

### 2026-11-12
- RAGAS 지표 도입 (사용자 요청: 자체 평가 반복 + LLM-as-Judge·RAGAS + 라운드별 리포트)
  - 지표 3개: Faithfulness(근거 충실도), Answer Relevancy(답 관련성, 임베딩 Titan v2), Context Precision(정답 없는 방식). Context Recall 은 모범 답안이 없어 제외
  - 근거(contexts)가 있는 문항만 계산 (거절·안내 문항은 근거가 없는 게 정답)
  - evaluation/ragas_eval.py 새로 만듦: RAGAS 0.4.3 collections API + Bedrock 어댑터(구조화 출력 LLM, 예비 모델 대체, Titan 임베딩)
  - 설치 문제: ragas 의 scikit-network 가 Python 3.14 설치 파일 없음 → --no-deps 설치 후 필요한 의존만 설치. ragas 가 찾는 langchain_community VertexAI 모듈은 빈 자리만 만들어 둠
  - 시험: 실제 풀이 충실도 0.62 / 지어낸 답 0.00 으로 구분됨
  - **1차 라운드 (round1_report.md)**: LLM-as-Judge **19/20** (6번 실패: 운세만 요청에서 search_reading_docs 미호출 + 근거에 없는 꾸밈말), RAGAS 근거 충실도 **0.49**, 답 관련성 **0.34**, 근거 정확도 **0.85** (근거 있는 8문항). 채점 중 예비 모델로 넘어간 호출 있음 (global 4.6, us 4.6, global 4.5 섞임)
  - 개선 1 (근거 충실도): agent.py 지켜야 할 것에 "풀이 문장은 도구 결과 문장을 옮기거나 줄여 쓰고 꾸밈말·새 해석을 덧붙이지 않는다" 추가
    - 근거 있는 8문항 --ragas: 근거 충실도 0.49 → **0.60**, 6번 통과, 답 관련성 0.34·근거 정확도 0.84 그대로
    - 전체 20문항: **20/20** (깨진 문항 없음) → 유지
  - 답 관련성이 낮은 원인 조사: 언어 문제 아님 (한국어 답에서도 한국어 질문을 만듦, 한국어 0.66 / 영어 0.78). **정책상 붙이는 재미 안내 문구가 회피형 답으로 읽혀 점수를 0.66 → 0.29~0.42 로 낮춤**
  - 측정 기준 변경 (사람 결정): RAGAS 계산 때만 안내 문구(※ 줄)를 빼고 잰다. 리포트에 기준을 적는다
    - 라운드마다 답·근거를 roundN_answers.json 으로 저장 (기준이 바뀌어도 같은 답으로 다시 계산), --rescore N 으로 다시 계산해 roundN_report.md 에 "측정 기준 변경 후 재계산" 절을 붙인다
    - 1차 답은 저장되지 않았었기에 LangSmith 실행 기록(09:30~09:42, 20건)에서 복원 → round1_answers.json. 6번 답이 리포트에 남은 답과 글자까지 같아 복원 확인
    - 2차 리포트의 1차 비교 표는 "당시 기준"과 "같은 기준 재계산"을 함께 보여 준다
- **src/ 도메인 폴더 리팩토링** (사용자 요청): shared·knowledge·face_analysis·reading·fortune·supervisor·guardrails·sharing·web
  - 도메인마다 tools/agent/prompts/schemas 를 함께 둔다. 공통(LLM 클라이언트·설정·메시지·위임)만 shared/
  - 제출 필수 src/agent.py·tools.py·retriever.py 와 실행용 src/server.py 는 다시 내보내기만 하는 진입점으로 남김 (uvicorn src.server:app 그대로)
  - 옛 subagents.py·guardrails.py·mailer.py 삭제, static/ → web/static/
  - 확인: 모든 프롬프트·규칙·FaceAnalysis 스키마가 옛 파일과 글자까지 같음, 모듈 30개 import, 도구 오프라인 결과 동일, 감독·단일 모드 생성, 서버 정적 경로·전체 풀이·고양이 사진 정상
  - CLAUDE.md 에 폴더 역할·배치 규칙·의존 방향 정의
- 어진 그림 경로를 코드에서도 정함 (사용자 요청): reading/tools.py 의 PORTRAIT_FILES (태조·영조·철종·고종)
  - kings.md 어진 필드를 먼저 보고, 없음이면 PORTRAIT_FILES 에서 왕 이름으로 찾음. 그림 파일이 실제로 있을 때만 경로를 줌
  - 화면은 근거 문장(contexts)에서 그림 경로를 찾으므로, 문서에 경로가 없으면 근거 문장에 "- 어진 그림: 경로" 한 줄을 덧붙임
  - 확인: 그림 있는 왕 4명, 철종·고종이 뽑히는 특징으로 도구·근거·화면 카드 모두 어진 경로 표시. 서버 재기동 후 두 그림 200 응답
- 리팩토링 뒤 경로별 8문항 확인 (--only 4,6,7,9,12,13,19,20): 3/8 이지만 **모델 하루 한도 때문에 무효**
  - 4·13·19 채점 모델 한도로 SKIP, 6 은 예비 모델까지 모두 한도라 에이전트가 답을 못 함, 9 는 답이 맞는데 채점이 "통과가 맞다"고 쓰고 실패로 판정(채점 오류)
  - 통과: 7(닮은 동물), 12(자료에 없는 점), 20(인젝션+건강). 한도가 풀린 뒤 전체 20문항 재측정 필요
  - 발견: 모든 모델이 한도에 걸리면 "Model call failed … ThrottlingException" 원문이 사용자에게 그대로 보임 → 고침 (아래)
- 사람이 .env 리전을 us-east-1 → **us-west-2** 로 변경 (하루 한도는 리전별). us-west-2 에서 global/us Sonnet 4.6, global Sonnet 4.5, Haiku 4.5, Titan v2 호출 가능 확인 (Sonnet 5·5.5 는 권한 없음). 코드 변경 없음
- **리팩토링 검증 (us-west-2, 전체 20문항): 19/20** (positive 8/8, negative 3/4, edge 5/5, guardrail 3/3)
  - 실패 10번: 답은 맞음(얼굴 없음 안내 + 재촬영·텍스트 안내 + "이마가 어떻게 생기셨나요?"). 채점이 질문 속 부위 언급을 위반으로 봄 (채점 지침과 어긋남)
  - 10번만 두 번 다시 → 둘 다 통과. 채점 변동으로 판단, 되돌리지 않음. 리팩토링으로 바뀐 동작 없음
  - 같은 유형의 채점 흔들림(9·10번, "이마" 언급)이 반복됨 → 채점 지침에 예시를 더 넣을지 사람 결정 필요
- **[사진:] 표기 대비책** (사용자 요청): image 필드가 비어 있고 question 이 [사진:images/파일명] 으로 시작하면 서버가 evaluation/images/ 의 사진을 읽어 쓴다
  - face_analysis/image.py image_from_notation, supervisor/graph.py ask 에서 호출, shared/config.py EVAL_IMAGES_DIR
  - 보안: 폴더 안 이미지 파일만 허용. ../../.env, src/server.py, test_queries.csv 같은 경로는 거부 확인
  - 채점 흉내 확인: 사진 9문항(1,2,3,9,10,11,16,18,19)을 input 그대로·image 없이 보냄 → **9/9 통과** (대비책 전에는 "사진이 전달되지 않음")
- 제출 요건 점검: question 만 보내는 규약 요청 정상. **[사진:] 표기를 question 에 그대로 보내면 사진이 전달되지 않아 사진 문항이 실패** → 서버 대비책 여부 사람 결정 필요. §4-3·§4-5 템플릿 원문 없음, README.md 없음
- 한도 오류 안내: guardrails 출력 검사에서 모델 오류 원문(Model call failed·ThrottlingException 등)을 "지금 이용하는 사람이 많아 … 잠시 뒤에 다시 시도해 주세요" 로 바꿈 (rules.MODEL_FAILURE·BUSY_ANSWER)
- 결과 화면 버튼 이름 "HTML로 저장" → "저장" (마우스 설명: 결과를 HTML 파일로 저장)
- E-mail 공유 기능 (사용자 요청): "저장"과 "닫기" 사이 버튼 → 받을 주소 입력 → 보내기
  - AWS 키에 SES 권한이 없어 SMTP 로 보냄. src/mailer.py 새로 만듦, POST /share-email 추가. 계정은 .env 의 SMTP_HOST·SMTP_PORT·SMTP_USER·SMTP_PASSWORD·MAIL_FROM (아직 미설정 → "설정이 아직 없어요" 안내)
  - 메일: 고정 제목, 본문은 요약(관상 유형·닮은 왕·동물·오늘 운세) + 재미 안내, 첨부는 결과 HTML (얼굴 사진 제외)
  - 악용 방지: 주소 형식 검사, 받는 사람 1명, 같은 접속처 1시간 5통, 첨부 3MB 이하
  - 확인: 가짜 메일 서버로 발송 성공·제목·첨부, 잘못된 주소·설정 없음·6번째 발송 차단 메시지, 화면 스크린샷
  - 사람이 .env 에 Gmail 앱 비밀번호 입력 → 서버 재기동 후 POST /share-email 로 보내는 계정 자신에게 실제 발송 성공 (첨부 194KB, 얼굴 사진 없음)
- (이어서) RAGAS 재계산
  - **1차 같은 기준 재계산 완료 (빈 값 0)**: 근거 충실도 **0.56**, 답 관련성 **0.33**, 근거 정확도 **0.79** (당시 기준 0.49 / 0.34 / 0.85)
    - 안내 문구를 빼도 전체 풀이(1~4번)의 답 관련성은 0.09~0.26 으로 낮음: 짧은 질문과 일곱 섹션 답의 차이가 주원인. 문구 영향은 짧은 답에서 큼
    - --rescore 는 이미 계산한 값은 두고 빈 값만 채우도록 바꿈 (8개 → 3개 → 1개 → 0개)
  - 첫 재계산은 한꺼번에 많이 불러 Throttling 으로 값 다수가 비어 무효 → 모든 모델이 막히면 기다렸다 다시 돌기(최대 4바퀴), 동시 계산 3→2, 비어 있는 값 수를 리포트에 표시. us Sonnet 4.6 은 오늘 하루 한도 도달
  - run_eval.py: --round 또는 --ragas 일 때 RAGAS 계산, 리포트에 RAGAS 요약·문항별 점수·지표 설명, 2차는 1차와 비교 표. runs.csv 에 round·RAGAS 평균 열 추가(기존 기록 유지). 채점 실패 시 멈추지 않고 SKIP, 요청 제한 시간 120→300초
- data/kings.md 사람이 25명으로 확장 → find_similar_king 이 같은 유형 안에서 특징 해시로 고르도록 변경 (같은 얼굴이면 같은 왕, 25명 모두 선택 가능 확인). 철종·고종 어진(퍼블릭 도메인) 추가로 그림 있는 왕 4명
- 관상 결과 HTML 다운로드 (사용자 요청): 전체 결과 시트 위쪽 "HTML로 저장" 버튼 → 관상결과_YYYY-MM-DD.html
  - 브라우저에서 만들어 바로 내려받는다 (서버에 저장하지 않음). 화면 CSS 를 넣고, 사진·어진 그림은 data URL 로 넣어 서버 없이 열린다. 바로가기 버튼은 뺀다
  - Edge headless 로 만든 파일을 열어 확인: 그림 2개 내장, 서버 경로 0, 약 200KB
- 결과 순서 변경 (사용자 요청): 닮은 조선의 왕을 닮은 동물보다 위로. 화면은 섹션을 정해진 순서로 정렬하고(에이전트 답 순서와 무관), agent.py 답 형식과 SERVICE.md 1-2 순서도 맞춤
- 테스트 이미지 9장 준비: 받은 사진 5장을 face_01~04·camera_01 로 이름 변경. dark_face(test7 어둡게+흐리게), two_people(test8+test9 나란히), cat·landscape(Pillow 로 그림) 생성. test1 은 AVIF 라 test1.jpg 로 변환 (예비)

### 2026-11-13
- **2차 자체 평가 (round2_report.md, --round 2)**: LLM-as-Judge **20/20** (positive 8/8, negative 4/4, edge 5/5, guardrail 3/3) → 목표 달성
  - RAGAS (근거 있는 8문항, 안내 문구 제외 기준): 근거 충실도 **0.68**, 답 관련성 **0.36**, 근거 정확도 **0.75**
  - 개선폭 (같은 기준 1차 대비): 통과 +1건(19→20), 근거 충실도 **+0.12**, 답 관련성 +0.04, 근거 정확도 -0.04
  - 개선 원인: 6번 통과(운세 보고에 특징별 문구), 근거 충실 규칙(꾸밈말 금지)으로 6번 충실도 0.17→0.50. 근거 정확도 하락은 특징별로 나눈 검색이 쓰지 않는 근거까지 가져오기 때문(다음 후보: MIN_SCORE 상향)
  - run_eval.py: 2차 비교 표에 "개선폭 (2차 − 같은 기준 1차)" 열 추가(_delta). 저장된 round2_report.md 는 다시 돌리지 않고 같은 값으로 표와 해석 문단을 더함
