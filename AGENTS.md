# AgentTrace Project Routing & Guidelines

이 문서는 AgentTrace 프로젝트에서 작업할 때 에이전트(AI)가 반드시 지켜야 할 행동 제약 조건과 규칙을 정의합니다.

---

## 🗺️ Documentation Map (참조 문서 지도)

상세 정보는 아래 전용 문서들을 가상환경 작업 및 분석 시 적극 참조하십시오.

* 🛠️ **[development.md](file:///Users/wolyong/workspace/AgentHub/agenttrace/docs/development.md)**: 패키지 관리(uv), 환경변수 설정, 구동 명령어 및 pytest 테스트 가이드.
* 📝 **[logging.md](file:///Users/wolyong/workspace/AgentHub/agenttrace/docs/logging.md)**: 중앙 structlog 설정, JSON 로깅 아키텍처 및 로그 필터 명령어 모음.
* ⚠️ **[troubleshooting_learnings.md](file:///Users/wolyong/workspace/AgentHub/agenttrace/docs/troubleshooting_learnings.md)**: 과거 개발 시 발생했던 고유 스코프 에러 및 라이브러리 충돌 디버깅 해결 로그.
* 📦 **[docs/reference](file:///Users/wolyong/workspace/AgentHub/agenttrace/docs/reference)**: 요구사항 스펙 및 MVP 설계 기준 문서의 로컬 복제본 리포지토리.

---

## 1. Context Handling & Reference (컨텍스트 관리)

- **검색/분석 필터링 활용**: 리포지토리 검색, 세어보기, 파싱 및 요약에는 대화에 소스를 직접 뿌리기보다 `context-mode` 및 배치 실행(`ctx_batch_execute`, `ctx_execute`)을 우선 사용하십시오.
- **문서 동기화**: 매 세션 시작 시 반드시 `rtk git -C docs/reference pull`을 실행하여 최신 참조 아티팩트를 획득한 후 해당 경로(`docs/reference/artifacts/current`)의 문서를 읽기 전용으로 참조하십시오.

## 2. MCP Server Routing (도구 연동)

- **GitHub MCP**: PR, 이슈, 커멘트 및 리뷰 관련 조사 작업 시 셸 커맨드 대신 GitHub MCP를 최우선으로 연동하여 사용하십시오. (기본 대상: `YonghoBae/agenttrace`)
- **LangChain Docs MCP**: LangChain, LangGraph, LangSmith 관련 API 변경이나 새로운 기능을 구현할 때, 반드시 `mcp__langchain_docs`를 이용해 문서를 최우선 검색하고 적용 방안을 검증하십시오. (파이썬 우선)

## 3. Development Workflow (개발 절차)

- **RTK 프록시**: 모든 터미널 명령어(git, pytest 등)는 반드시 `rtk` 접두사를 붙여 토큰 소비를 최소화해야 합니다. (예: `rtk git status`)
- **TDD (테스트 우선)**: 코드를 수정하거나 노드 동작을 바꾸기 전에 테스트 코드를 먼저 추가 혹은 보완하십시오.
- **점진적 코드 수정**: 대량의 파일을 전체 덮어쓰기보다 `replace_file_content` 및 `multi_replace_file_content`로 변경이 필요한 코드 블록만 치환하여 정확도를 높이고 아웃풋 토큰을 절감하십시오.
- **종속성 관리**: 패키지 설치에는 반드시 `uv`를 사용하고 변경 시 `uv.lock`이 커밋에 보장되게 하십시오.

## 4. Node Logging Pattern (노드 로깅 지침)

새로운 파이프라인 노드 작성 시 또는 기존 노드 개선 시 다음의 구조화 로그 패턴을 엄격하게 구현하십시오.

```python
import time
from agenttrace.logging_config import get_logger
from agenttrace.agents.analysis.state import AnalysisState

logger = get_logger(__name__)

def my_node(state: AnalysisState) -> AnalysisState:
    _t = time.perf_counter()
    run_id = state.get("run_id", "-")
    
    # run_id와 현재 노드명을 항상 구조화 필드로 바인딩
    log = logger.bind(node="my_node", run_id=run_id)
    log.info("시작")
    
    # ... 노드 전용 구현 로직 ...
    
    # 노드 종료 시 성공 결과 주요 정보를 딕셔너리로 바인딩하여 1회 완료 로그 생성
    log.info(
        "완료", 
        key=value,  # 성공 결과 지표 등
        duration_ms=int((time.perf_counter() - _t) * 1000)
    )
    return result
```

- LLM 실패·fallback 처리 시에는 `log.warning()`, 코드 예외 상황에는 `log.error()`를 사용하며 context-specific 정보 외의 API 키 등 민감 정보가 로그 문자열에 포함되어서는 안 됩니다.
