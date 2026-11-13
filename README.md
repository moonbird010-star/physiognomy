# 미니 PJT: 내가 왕이 될 상인가? — 재미로 보는 관상 에이전트

## 무엇을 푸나
관상 풀이가 부위별로 흩어져 있어 내 얼굴에 맞춰 한 번에 보기 어려운 문제를, 얼굴 사진 한 장(또는 생김새 몇 마디)으로 근거 문서에 기반한 풀이·닮은 조선의 왕·닮은 동물·운세를 한 번에 보여 주는 재미용 에이전트로 푼다.

## 활용한 패턴 (Day 1~7)
- Day 1: LCEL chain (Pydantic 구조화 출력) — 사진 분석을 `RunnableLambda(메시지) | 모델.with_structured_output(FaceAnalysis)` 체인으로 만들고, 예비 모델을 `.with_fallbacks()` 로 묶었다 (`src/face_analysis/tools.py`)
- Day 2: RAG (쿼리 확장) — `data/` 해석 문서를 `##` 섹션 단위로 나누고, 질의를 특징별로 쪼개 각각 찾으며, 점수가 낮으면 버려 "자료에 없는 특징"을 지어내지 않는다 (`src/knowledge/retriever.py`). 하이브리드·리랭킹은 검토 후 보류 (아래 회고)
- Day 3: ReAct (도구 자율 선택) — `create_agent` 가 질문에 따라 도구를 0~5개 스스로 고른다 (예: 닮은 동물만 물으면 `find_similar_animals` 하나)
- Day 4: 도구 다중 — 사진 분석·해석 검색·닮은 왕·닮은 동물·운세(날짜 계산) 도구 5개를 전체 풀이 한 번에 결합한다
- Day 5: 가드레일 (PII·프롬프트 인젝션 방어) — 입력 검사(인젝션·판단 금지 주제 표시), 출력 검사(금지 판단 차단·단정 표현 완화·재미 안내·모델 오류 안내)를 코드로 둔다 (`src/guardrails/`)
- Day 5: 미들웨어 (요약·마스킹·재시도) — `PIIMiddleware`(휴대폰·주민번호·이메일 가림), `SummarizationMiddleware`, `ModelRetry`·`ToolRetry`, `ModelFallbackMiddleware`(하루 토큰 한도 대비 예비 모델)
- Day 6: Multi-Agent Supervisor — 감독 에이전트가 `photo_agent`·`reading_agent`·`fortune_agent` 서브 에이전트에게 나눠 맡기고, 풀이·운세는 병렬로 처리한다 (`src/supervisor/`, 각 도메인 `agent.py`)
- Day 7: Observability · Trace — LangSmith 에 감독·서브 에이전트 실행을 남기고(사진 분석 호출만 추적 제외), 응답 `trace` 에 서브 에이전트와 도구 호출 순서를 담는다
- Day 7: 평가 (RAGAS · LLM-as-Judge) — 인-아웃 세트 20문항을 규칙 검사 + LLM 채점으로 재고, RAGAS 3개 지표를 라운드 리포트로 남긴다 (`evaluation/`)
- 쓰지 않은 패턴: MCP(서비스에 필요 없음), HITL(승인할 위험 작업이 없음), 장기 메모리(사용자 기록을 저장하지 않는 정책)

## 아키텍처
```
브라우저 (src/web/static/index.html: 사진 선택 · 카메라 촬영 · 대화 · 저장 · E-mail 공유)
   │  POST /query {question, image?, session_id?}         POST /share-email
   ▼                                                         ▼
FastAPI (src/web/app.py) ──────────────────────────────▶ sharing/mailer.py (Gmail SMTP, 사진 제외)
   ▼
ask()  사진은 요청 동안 메모리(contextvar)에만, [사진:images/…] 표기면 evaluation/images 에서 읽음
   ▼
[입력] PII 가림 → input_guard
   ▼
감독 에이전트 (Supervisor, checkpointer = session_id 대화 기억)
   ├─ photo_agent   → analyze_face_photo  (LCEL 비전 체인: 얼굴 없음·여러 명·어두움 판정, 특징 추출)
   ├─ reading_agent → search_reading_docs · find_similar_king · find_similar_animals ─┐
   └─ fortune_agent → get_fortune ─────────────────────────────────────────────────┤ 병렬
                                                       data/*.md 해석 문서 (RAG) ◀─┘
   ▼
[출력] output_guard (금지 판단 차단 · 단정 표현 완화 · 재미 안내 · 모델 오류 안내)
   ▼
응답 {answer, contexts, trace} → 화면이 일곱 섹션을 카드로 그림

모델: Bedrock Claude Sonnet 4.6 (global 경로) → 예비 us Sonnet 4.6 → global Sonnet 4.5 (자동 대체)
```

`src/` 는 업무 도메인별 폴더로 나뉜다: `shared`(LLM 클라이언트·설정·위임), `knowledge`(RAG), `face_analysis`, `reading`, `fortune`, `supervisor`, `guardrails`, `sharing`, `web`. 폴더 역할과 배치 규칙은 `CLAUDE.md` 에 있다.

## 실행 방법
1. 가상 환경에서 의존 패키지를 설치한다 (Python 3.14 기준)
   ```bash
   pip install -r requirements.txt
   pip install --no-deps ragas==0.4.3   # 평가용. scikit-network 가 3.14 용 설치 파일이 없어 의존성 없이 설치
   ```
2. 프로젝트 루트에 `.env` 를 만든다 (커밋하지 않는다)
   ```
   AWS_ACCESS_KEY_ID=…
   AWS_SECRET_ACCESS_KEY=…
   AWS_DEFAULT_REGION=us-west-2
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=…
   LANGSMITH_PROJECT=…
   JUDGE_MODEL_ID=global.anthropic.claude-sonnet-4-6   # 평가 채점 모델
   # 선택: MODEL_ID, FALLBACK_MODEL_IDS (모델 변경), AGENT_MODE=single (단일 에이전트로 되돌리기)
   # 선택: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM (E-mail 공유. Gmail 은 앱 비밀번호)
   ```
3. 서버를 띄운다
   ```bash
   python -m uvicorn src.server:app --port 8000
   ```
4. 브라우저에서 `http://localhost:8000/` 을 연다 (카메라는 localhost·HTTPS 에서만 켜진다). API 문서는 `http://localhost:8000/docs`
5. 평가 (서버가 떠 있는 상태에서)
   ```bash
   python evaluation/run_eval.py --note "고친 내용"     # 루프용: LLM-as-Judge
   python evaluation/run_eval.py --round 1 --note "…"   # 제출용 1차 리포트 + RAGAS
   python evaluation/run_eval.py --round 2 --note "…"   # 제출용 2차 리포트 + RAGAS + 1차 비교
   python evaluation/run_eval.py --rescore 1            # 저장된 1차 답으로 RAGAS 만 다시 계산
   ```

## RAGAS 평가 결과
1차 라운드 답(근거가 있는 8문항)을 같은 측정 기준(정책 안내 문구 제외)으로 계산한 값이다. 채점 LLM: Bedrock Claude Sonnet, 임베딩: Titan v2.
- context_recall: 측정하지 않음 — 모범 답안(reference)이 필요한데 인-아웃 세트에는 기대 동작만 있다
- context_precision: 0.79
- faithfulness: 0.56
- answer_relevancy: 0.33
- 참고: 1차 당시 기준(안내 문구 포함)은 faithfulness 0.49 · answer_relevancy 0.34 · context_precision 0.85. 개선 1(아래) 뒤 같은 8문항의 faithfulness 는 0.60 (당시 기준)
- 거절·안내 문항(고양이 사진, 신원 질문 등)은 근거가 없는 것이 정답이라 RAGAS 를 계산하지 않는다
- answer_relevancy 가 낮은 이유: "제 관상 봐주세요" 같은 짧은 질문에 일곱 섹션으로 답하는 구조 때문이다. 정책 안내 문구도 회피형 답으로 읽혀 점수를 깎아, 측정할 때만 그 줄을 뺀다
- 2차 라운드 RAGAS 는 `--round 2` 실행 뒤 `evaluation/round2_report.md` 에 1차와 비교 표로 남는다 (아직 실행 전)

## 인-아웃 세트 통과율 (자체 평가)
- 1차 (Day 9 종료): 19 / 20 통과 (`evaluation/round1_report.md`, 6번 실패: 운세만 요청에서 해석 문서를 찾지 않고 근거에 없는 꾸밈말)
- 2차 (Day 10 개선 후): 아직 실행 전 (`--round 2` 예정). 개선 뒤 루프 전체 실행 기록: 20 / 20 (2026-11-12 09:57), 리팩토링·리전 변경 뒤 19 / 20 (10번은 채점 흔들림으로, 단독 재실행 2회 모두 통과)
- 개선폭: +1 건 (1차 대비 루프 기록 기준. 주요 개선 사항: 풀이 문장은 도구 결과를 옮기거나 줄여 쓰고 꾸밈말을 덧붙이지 않도록 지시문 보강 → faithfulness 0.49 → 0.60, 6번 통과)
- 그 전 루프 기록 (Day 8): 14 → 15 → 19 → 20 / 20 (`evaluation/runs.csv`)
  - 일부 특징만 말해도 해석 문서를 먼저 찾고 바로 답하기 (6·8·12·17번)
  - 신원 질문·남의 사진은 도구 없이 거절 (19번)
  - 채점 지침: 질문·안내 속 부위 이름은 금지 항목 위반이 아님 (9·10번)
- 목표: 20문항 중 17건 이상 + guardrail·negative 전부 통과

## 트라이앤에러 회고
- 시도했지만 실패한 접근 · 왜 실패했는가
  - 사진 속 얼굴 수만 세서 여러 명이면 거절 → 교실에서 찍은 웹캠 사진이 배경 사람까지 세어(2명, 10명) 모두 거절됨. "주인공 얼굴이 하나로 분명한가"로 판정을 바꿨다
  - 벡터 검색(Titan 임베딩) 단독 → "웃상", "복스럽다" 같은 바꿔 말한 표현은 잘 찾지만, 문서에 없는 점·주름에도 가장 가까운 섹션을 근거로 가져와 "지어내지 않기"를 깼다. 점수 기준으로도 걸러지지 않아 보류
  - 어진이 없는 왕은 구글 이미지 검색으로 보여 주기 → 찾히는 것이 현대 표준영정(저작권)이나 사극 배우 사진(초상권)이라 채택하지 않았다
  - `us.` 경로 모델 하나만 사용 → 평가를 반복하다 분당·하루 토큰 한도에 걸려 서비스가 멈췄다
  - 안내 문구를 포함한 채 RAGAS 측정 → 정책 문구가 회피형 답으로 읽혀 answer_relevancy 가 절반가량 깎였다
  - Amazon SES 로 메일 발송 → AWS 키에 권한이 없어 SMTP(Gmail 앱 비밀번호)로 바꿨다
- 최종 채택한 접근 · 왜 그것으로 갔는가
  - 키워드(글자 묶음) 검색 + 특징별 질의 분해 + 점수 하한: 사진·대화 모두 에이전트가 특징을 정해진 표현으로 바꿔 넘기므로 충분했고, 문서에 없는 특징을 확실히 걸러 낸다
  - Multi-Agent Supervisor: 사진·풀이·운세를 나눠 맡겨 풀이와 운세를 병렬로 처리하고, trace 에 서브 에이전트와 도구 순서를 남긴다 (`AGENT_MODE=single` 로 되돌릴 수 있게 유지)
  - 모델 자동 대체(global Sonnet 4.6 → us Sonnet 4.6 → global Sonnet 4.5) + SDK 재시도 축소: 한 모델이 한도에 걸려도 서비스가 이어진다
  - 닮은 왕은 얼굴이 아닌 관상 유형(성향)으로 고르고, 원본 어진이 남은 왕(태조·영조·철종·고종)만 퍼블릭 도메인 그림을 보여 준다
  - 사진은 메시지·대화 기억·로그·LangSmith 에 넣지 않고 요청 동안 contextvar 로만 넘긴다
  - 한 바퀴에 원인 하나만 고치고, 실패 문항 → 전체 순서로 다시 재는 평가 루프 (점수가 떨어지면 되돌리기)
- 남은 한계 · 향후 개선 방향
  - LLM 채점이 같은 답을 실행마다 다르게 판정하는 일이 있다 (9·10번 "이마" 언급). 채점 지침에 예시를 더하거나 여러 번 채점해 다수결로 정할 수 있다
  - 하루 토큰 한도 때문에 전체 평가·RAGAS 를 자주 돌리기 어렵다. 응답도 전체 풀이 기준 40초 이상 걸린다 → 기다리는 동안 진행 단계를 보여 주는 화면 개선
  - answer_relevancy 는 일곱 섹션 전체 풀이 구조와 잘 맞지 않는다. 답 첫 줄에 질문에 대한 직접 요약을 두는 방식을 검토
  - 바꿔 말한 표현을 놓치지 않도록 하이브리드 검색(키워드 + Titan 벡터, RRF)을 넣되, "자료에 없음" 판정은 키워드 기준을 유지
  - 음성으로 생김새를 말하는 입력(브라우저 음성 인식), 다크 모드 등 화면 보강

## 핵심 코드 위치
- `src/agent.py:5` — 메인 에이전트 그래프 진입점 (실제 코드: `src/supervisor/graph.py:39` build_agent, `:64` ask)
- `src/tools.py:12` — 도메인 도구 5개 목록 (실제 코드: `src/face_analysis/tools.py:31`, `src/reading/tools.py`, `src/fortune/tools.py`)
- `src/retriever.py:5` — RAG 파이프라인 진입점 (실제 코드: `src/knowledge/retriever.py:45` search, `:24` load_chunks)
- `src/face_analysis/tools.py:24` — LCEL 비전 체인 (예비 모델 대체 포함)
- `src/shared/delegation.py:39` — 서브 에이전트 위임과 trace·contexts 모으기
- `src/guardrails/middleware.py:79` — 가드레일·미들웨어 묶음 (`:36` input_guard, `:55` output_guard)
- `src/shared/llm.py:18` — 모델 ID 와 예비 모델 순서 (`.env` 로 변경)
- `evaluation/run_eval.py` — LLM-as-Judge 평가와 라운드 리포트, `evaluation/ragas_eval.py` — RAGAS 지표
