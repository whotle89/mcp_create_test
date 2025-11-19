# Agent Orchestration System

별도 시스템 레이어로 UI 에이전트와 Logic 에이전트의 충돌을 방지하고 원활한 협업을 보장하는 오케스트레이션 시스템입니다.

## 목표

- 서브에이전트(ui-implementer, feature-logic-implementer) 간의 충돌 방지
- 명확한 실행 순서 보장 (UI → Backend)
- 필수 파일 검증 및 완료 확인
- 파일 수정 권한 제어
- 실시간 모니터링 및 메트릭 수집

## 시스템 구조

```
agent_orchestration_system/
├── agent_router.py          # 라우팅 로직 및 검증
├── main.py                  # 오케스트레이터 (실행 관리)
├── api_interface.py         # REST API 인터페이스
├── cli_interface.py         # CLI 인터페이스
├── monitoring.py            # 모니터링 및 메트릭
├── config.py                # 설정 관리
├── test_agent_system.py    # 테스트 스위트
└── requirements.txt         # 의존성
```

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 확인

```bash
python config.py
```

## 사용법

### CLI 인터페이스

#### 기본 사용

```bash
# 요청 처리
python cli_interface.py process "시간 거래 기능 만들어줘"

# 특정 경로 지정
python cli_interface.py process "Supabase 연결해줘" --path app/time-slots

# 완료 검증
python cli_interface.py verify ui-implementer app/time-slots

# 메트릭 확인
python cli_interface.py metrics

# 히스토리 내보내기
python cli_interface.py history --output history.json
```

#### 대화형 모드

```bash
python cli_interface.py interactive
```

### API 인터페이스

#### 서버 실행

```bash
python api_interface.py
# 또는
uvicorn api_interface:app --reload --port 8000
```

#### API 문서

서버 실행 후 브라우저에서 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### API 엔드포인트

**요청 처리:**
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "시간 거래 기능 만들어줘",
    "context": {"current_path": "app/time-slots"}
  }'
```

**완료 검증:**
```bash
curl -X POST http://localhost:8000/verify-completion \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "ui-implementer",
    "feature_path": "app/time-slots"
  }'
```

**파일 작업 확인:**
```bash
curl -X POST http://localhost:8000/check-file-operation \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "feature-logic-implementer",
    "operation": "create",
    "file_path": "app/time-slots/api.ts"
  }'
```

**메트릭 조회:**
```bash
curl http://localhost:8000/metrics
```

### Python 코드에서 직접 사용

```python
from main import AgentOrchestrator

# 오케스트레이터 초기화
orchestrator = AgentOrchestrator()

# 요청 처리
result = orchestrator.process_request("시간 거래 기능 만들어줘")

print(f"Agent: {result.agent}")
print(f"Status: {result.status}")
print(f"Message: {result.message}")

# 완료 검증
from pathlib import Path
verification = orchestrator.verify_agent_completion(
    "ui-implementer",
    Path("app/time-slots")
)

# 메트릭 확인
metrics = orchestrator.get_metrics()
print(f"Success Rate: {metrics['success_rate']:.1%}")
```

## 핵심 기능

### 1. 자동 라우팅

사용자 요청을 분석하여 적절한 에이전트로 라우팅:

- **UI 우선**: 새 기능은 항상 UI 에이전트부터 시작
- **백엔드 검증**: UI 기반이 없으면 백엔드 에이전트 실행 차단
- **수정 요청 분석**: 기존 기능 수정 시 적절한 에이전트 선택

### 2. 선행 조건 검증

에이전트 실행 전 필수 파일 확인:

```python
# feature-logic-implementer 실행 전 확인
✓ types.ts
✓ api.ts
✓ components/
```

### 3. 완료 검증

에이전트 완료 후 필수 산출물 확인:

```python
# ui-implementer 완료 확인
✓ types.ts 생성됨
✓ api.ts 생성됨 (TODO 마커 포함)
✓ components/ 디렉토리 생성됨
```

### 4. 충돌 방지

파일 수정 권한 제어:

- **UI 에이전트**: types.ts, api.ts, components/, page.tsx 수정 가능
- **Logic 에이전트**: lib/services/, lib/domain/, api.ts 구현만 수정 가능
- **금지 작업**:
  - Logic 에이전트의 UI 파일 수정
  - api.ts 함수 시그니처 변경
  - 중복 파일 생성

### 5. 모니터링

실시간 메트릭 수집 및 대시보드:

```bash
# 대시보드 표시
python -c "from monitoring import *; c = MetricsCollector(); Dashboard(c).display()"

# 알림 확인
python -c "from monitoring import *; c = MetricsCollector(); AlertSystem(c).display_alerts()"
```

## 테스트

### 전체 테스트 실행

```bash
pytest test_agent_system.py -v
```

### 커버리지 포함

```bash
pytest test_agent_system.py -v --cov=. --cov-report=html
```

### 특정 테스트만 실행

```bash
# 라우팅 테스트
pytest test_agent_system.py::TestRouting -v

# 충돌 방지 테스트
pytest test_agent_system.py::TestConflictPrevention -v
```

## 설정

### 환경 변수

```bash
# .env 파일 또는 환경 변수로 설정

# 라우팅 규칙
STRICT_AGENT_ROUTING=true
REQUIRE_UI_FIRST=true
VERIFY_UI_MANDATORY_FILES=true
PROTECT_UI_FILES=true

# 로깅
LOG_LEVEL=INFO

# API
API_PORT=8000
```

### 설정 파일

```bash
# config.json 생성
python config.py

# config.json 편집 후 로드
python -c "from config import Config; config = Config.load(Path('config.json'))"
```

## 라우팅 규칙

### Rule #1: UI 에이전트 우선 실행

```python
요청: "시간 거래 기능 만들어줘"
결정: ui-implementer ✓
이유: 새 기능은 UI부터 시작
```

### Rule #2: 백엔드 에이전트는 UI 기반 필요

```python
요청: "Supabase 쿼리 구현해줘"
검사: types.ts, api.ts, components/ 존재?
  - 존재 → feature-logic-implementer ✓
  - 없음 → BLOCKED ✗
```

### Rule #3: UI 에이전트 필수 파일 생성

```python
완료 조건:
1. types.ts 생성
2. api.ts 생성 (🔌 INTEGRATION POINT 포함)
3. components/ 디렉토리 생성

미충족 시 → BLOCKED ✗
```

## 메트릭

추적되는 주요 메트릭:

- **total_requests**: 전체 요청 수
- **routed_to_ui**: UI 에이전트로 라우팅된 수
- **routed_to_backend**: Logic 에이전트로 라우팅된 수
- **blocked_missing_prerequisites**: 선행 조건 미충족으로 차단된 수
- **blocked_incomplete_ui**: 불완전한 UI로 차단된 수
- **blocked_file_conflicts**: 파일 충돌로 차단된 수
- **successful_collaborations**: 성공적인 협업 수
- **success_rate**: 성공률 (차단률의 역수)

## 예제 시나리오

### 시나리오 1: 새 기능 생성 (UI → Backend)

```bash
# Step 1: UI 생성 요청
$ python cli_interface.py process "시간 거래 기능 만들어줘"
✅ Routing to ui-implementer
Task: Create UI foundation for feature
Location: app/time-slots

# Step 2: UI 완료 검증
$ python cli_interface.py verify ui-implementer app/time-slots
✅ ui-implementer completed successfully
All required files created

# Step 3: 백엔드 구현 요청
$ python cli_interface.py process "Supabase 연결해줘" --path app/time-slots
✅ Routing to feature-logic-implementer
Found UI foundation:
- types.ts: ✓
- api.ts: ✓
- components/: ✓
```

### 시나리오 2: 백엔드 우선 시도 (차단됨)

```bash
$ python cli_interface.py process "Supabase 인증 로직 구현해줘"
❌ Cannot proceed with backend implementation

UI foundation not found at: app/auth

Required files:
- types.ts (TypeScript interfaces)
- api.ts (integration layer)
- components/ (UI components)

Next steps:
1. First, run ui-implementer to create the UI structure
2. Then, run feature-logic-implementer to add backend logic
```

### 시나리오 3: 파일 충돌 감지

```bash
$ python cli_interface.py check feature-logic-implementer modify app/time-slots/components/Form.tsx
❌ Operation forbidden

FORBIDDEN: feature-logic-implementer cannot modify app/time-slots/components/Form.tsx.
This is UI territory. Request ui-implementer to make changes.
```

## 아키텍처

```
┌─────────────┐
│   사용자     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  AgentOrchestrator (main.py) │
│  - 전체 워크플로우 관리       │
│  - 에이전트 실행 조율          │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  AgentRouter (agent_router.py)│
│  - 요청 분석 및 라우팅        │
│  - 선행 조건 검증             │
│  - 완료 검증                  │
│  - 충돌 방지                  │
└──────────┬──────────────────┘
           │
           ├─────────────────┐
           ▼                 ▼
    ┌─────────────┐   ┌──────────────────┐
    │ui-implementer│   │feature-logic-impl│
    └─────────────┘   └──────────────────┘
```

## 문제 해결

### Q: "Cannot run feature-logic-implementer" 오류

**A:** UI 기반이 필요합니다. 먼저 ui-implementer를 실행하여 types.ts, api.ts, components/를 생성하세요.

### Q: "Cannot complete ui-implementer task" 오류

**A:** 필수 파일이 누락되었습니다. types.ts, api.ts (TODO 마커 포함), components/ 모두 생성했는지 확인하세요.

### Q: "FORBIDDEN: cannot modify" 오류

**A:** 에이전트가 권한 없는 파일을 수정하려 합니다.
- Logic 에이전트는 UI 파일(components/, page.tsx)을 수정할 수 없습니다.
- UI 변경이 필요하면 ui-implementer를 사용하세요.

### Q: 메트릭이 수집되지 않음

**A:** config.py에서 `METRICS_ENABLED = True`로 설정되어 있는지 확인하세요.

## 기여

이슈나 개선 사항이 있으면 GitHub Issues에 등록해주세요.

## 라이선스

MIT License
