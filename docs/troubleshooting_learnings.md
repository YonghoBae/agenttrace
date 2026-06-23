# Troubleshooting & Learnings Log

이 문서는 AgentTrace 개발 과정에서 발견된 중요 시행착오, 트러블슈팅 내역, 그리고 디자인 패턴 상의 레슨 런(Lesson Learned)을 기록하여 미래의 에이전트와 개발자가 동일한 실수를 반복하지 않도록 돕는 로그입니다.

---

## 1. structlog 설정 시 PrintLogger 명칭 처리 에러 (AttributeError)

* **문제 현상**: 파이프라인 로깅을 위해 `structlog` 설정을 적용한 후 테스트 실행 시 `PrintLogger`에 `name` 속성이 없다는 `AttributeError` 발생.
* **원인**:
  ```python
  structlog.configure(
      processors=[
          structlog.stdlib.add_logger_name,  # <- 원인
          ...
      ],
      logger_factory=structlog.PrintLoggerFactory()  # PrintLogger 반환
  )
  ```
  `structlog.stdlib.add_logger_name` 프로세서는 표준 라이브러리(stdlib) 스타일의 로거를 상정하므로 로거 객체에 `.name` 속성이 존재해야 합니다. 하지만 `PrintLoggerFactory`가 만드는 `PrintLogger`는 이 속성이 없어 에러가 발생합니다.
* **해결 방법**:
  `structlog` 설정의 `processors` 체인에서 `structlog.stdlib.add_logger_name`을 제거하여 명칭을 추가하는 프로세스를 우회했습니다.
* **레슨 런**: `PrintLogger`를 로거 팩토리로 쓸 때는 표준 라이브러리 의존적인 프로세서(예: `stdlib` 네임스페이스 하위 프로세서)의 동적 속성 접근을 주의해야 합니다.

---

## 2. 노드 내 레거시 함수(Legacy functions) 호출 시 스코프 에러 (NameError)

* **문제 현상**: `evidence_scout` 노드에 로깅을 추가한 뒤 테스트 실행 시 `NameError: name 'log' is not defined`로 실패.
* **원인**:
  ```python
  def evidence_scout(state):
      _t = time.perf_counter()
      log = logger.bind(node="evidence_scout")
      ...
      if not task:
          return _legacy_evidence_scout(state)  # 내부에서 log, _t 호출
  ```
  별도 모듈 레벨 함수로 정의된 `_legacy_evidence_scout` 함수 안에서 상위 로컬 스코프의 `log` 및 `_t`를 직접 참조하여 발생한 스코프 범위 에러입니다.
* **해결 방법**:
  `_legacy_evidence_scout(state, log, _t)` 형태로 로깅 컨텍스트(`log`)와 시간 측정 시작점(`_t`)을 인자로 명시적으로 넘겨주도록 함수 시그니처와 호출부를 수정했습니다. `_legacy_quality_gate` 역시 동일하게 보완했습니다.
* **레슨 런**: LangGraph 노드 내부에서 조건에 따라 별도 헬퍼 함수나 레거시 로직 함수로 분기할 경우, 로컬 바인딩 로거(`log`)와 측정 시작 시각(`_t`)을 인자로 투명하게 전달해야 합니다.

---

## 3. Worker 내 잡(Job) 데이터베이스 외래키 방어코드

* **문제 현상**: 과도기적/독립적 워커 런 실행 시 parent 레코드 누락으로 인한 외래키(Foreign Key) 무결성 에러 발생 가능성 존재.
* **해결 방법**:
  [worker.py](file:///Users/wolyong/workspace/AgentHub/agenttrace/src/agenttrace/app/worker.py) 내 `run_analysis_pipeline` 진입 시 `repositories` 및 `repository_snapshots` 테이블에 방어적 삽입(`INSERT ON CONFLICT DO NOTHING`)을 수행하여 외래키 에러를 예방합니다.

---

## 4. pytest 환경에서의 structlog sys.stderr 바인딩 closed file 에러

* **문제 현상**: CLI 표준 출력 오염 방지를 위해 로깅 출력을 `sys.stderr`로 변경 후, pytest 실행 시 일부 CLI 테스트에서 `ValueError: I/O operation on closed file.` 발생.
* **원인**:
  pytest는 각 테스트 진행 시 표준 입출력 스트림(`sys.stdout`, `sys.stderr`)을 동적으로 캡처하고 테스트 종료 시 닫습니다. `setup_logging` 호출 단계에서 `structlog.PrintLoggerFactory(sys.stderr)` 형태로 넘기면, 해당 시점에 바인딩되어 있던 특정 파일 객체(`sys.stderr`)를 상시 캐싱하게 됩니다. 이로 인해 다음 테스트 차례에 이미 닫혀버린 파일 객체에 접근을 시도하여 오류가 유발됩니다.
* **해결 방법**:
  런타임에 동적으로 `sys.stderr`를 조회하여 기록하는 `StderrPrintLogger` 클래스를 구현하고, `logger_factory`를 `lambda *args, **kwargs: StderrPrintLogger()` 형태로 동적 할당하도록 구조화하여 문제를 해결했습니다.
* **레슨 런**: 글로벌 싱글톤이나 한 번만 설정되는 프레임워크 로깅 초기화 시, 테스트 러너가 가로채어 관리하는 시스템 스트림 파일 객체를 직접 참조 보관해서는 안 됩니다. 반드시 지연 평가(Lazy evaluation)를 통해 런타임의 최신 파일 핸들을 획득하도록 구현해야 합니다.

