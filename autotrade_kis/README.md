# autotrage_kis — 개발 단계 체크리스트 (Day 1–Day 5)

목표
- 한국투자증권 Open API 기반 자동매매 시스템 구축
- 저빈도(DAILY 1회/일 + WEEKLY 0-1회/주) 전략을 안전장치 포함해 구현
- 실전 전환 전 모의투자에서 충분히 검증

문서/스펙(필수)
- STRATEGY.md: 전략 설명(사람이 읽는 문서)
- SPEC.md: 규칙/수치/변수명 고정(구현 스펙)
- ACCEPTANCE.md: 통과 조건(테스트 명세)
- src/strategy_config.py: 전략 파라미터 상수

핵심 상태 변수(용어 통일)
- position_state: NONE | DAILY | WEEKLY
- daily_entry_taken: DAILY 당일 진입 1회 잠금
- daily_stop_triggered: 손절 발생 후 당일 신규 진입 차단 플래그
- weekly_mode: 1W | 2_3W
- weekly_signal_h1: H1(60분봉)에서 bb_reentry_h1 AND macd_recover_h1 AND vol_confirm_h1

---

## Day 1 — API 스모크 테스트 (주문 금지)
목표
- 인증/시세/캔들 조회가 정상인지 확인

할 일
- .env / .gitignore 보안 세팅 (키/토큰 로그 출력 금지)
- 토큰 발급 구현
- 현재가 조회 구현
- M5(5분봉) 캔들 조회 구현
- D1(일봉) 캔들 조회 구현
- main_smoketest.py 실행 시 아래 순서로 성공 로그 출력
  - 토큰 OK
  - 현재가 OK
  - M5 캔들 OK
  - D1 캔들 OK
- data/에 캔들 csv 저장
- logs/에 실행 로그 저장

완료 기준
- 위 4개 조회 성공 + 로그/데이터 파일 생성 확인

---

## Day 2 — 데이터 파이프라인 + 지표 계산 + 신호 생성 (주문 금지)
목표
- 전략 판단에 필요한 캔들/지표/신호가 일관되게 생성되게 만들기

할 일
- 캔들 수집 모듈 정리
  - M5(진입/청산)
  - H1(주간 신호 판단)
  - D1(환경 판단)
  - (선택) W1(weekly_mode=2_3W 환경 판단)
- 지표 계산 모듈 구현(주간 신호용, H1 기준)
  - 볼린저 밴드(BB)
  - MACD
  - 거래량 평균(vol_ma)
- 신호 생성만 구현(주문 X)
  - DAILY
    - opening_high 계산
    - 돌파 조건 True/False 출력
  - WEEKLY (H1 완성봉 기준)
    - bb_reentry_h1 True/False
    - macd_recover_h1 True/False
    - vol_confirm_h1 True/False
    - weekly_signal_h1 = AND 결과 출력
- 신호 결과를 data/에 저장(csv)
- 로그에 “왜 True/False인지” 근거 기록

완료 기준
- 동일 캔들 입력 → 동일 지표/신호 결과 재현 가능
- weekly_signal_h1은 H1 미완성봉으로 True가 되지 않음

---

## Day 3 — 모의투자 주문 1회 + 체결/잔고 동기화
목표
- 주문 넣고 상태를 정확히 추적할 수 있게 만들기

할 일
- 주문(매수/매도) 함수 구현 (모의투자)
- 주문 후 동기화 루틴 구현
  - 미체결 조회 → 체결 확인 → 잔고 확인
- 중복 주문 방지
  - 주문번호/원주문번호 저장
- 상태 전이(state transition) 구현
  - 포지션 진입 시 position_state = DAILY 또는 WEEKLY
  - 포지션 청산 시 position_state = NONE
- 1포지션 정책 강제
  - position_state != NONE이면 신규 진입 금지
- 손절 후 당일 정지 플래그 동작 확인
  - 손절 발생 시 daily_stop_triggered = True
- ACCEPTANCE.md의 A-1 ~ A-4 항목 충족 확인

완료 기준
- 모의에서 1회 매수 → 체결 확인 → 잔고 반영 확인 → 매도까지 성공
- 로그에 주문/체결/잔고 반영 흐름이 명확히 남음

---

## Day 4 — DAILY 전략 자동 실행 (WEEKLY OFF)
목표
- 변동성 돌파(DAILY)를 완전 자동으로 안전하게 실행

할 일
- 장 시작 감지 + 오프닝 레인지(opening_high) 계산
- DAILY 트리거 발생 시 1회 진입
  - 진입 시 daily_entry_taken = True
  - position_state = DAILY
- TP/SL/EOD 청산 구현
  - TP/SL 도달 시 즉시 청산
  - 장 종료 전 강제 청산(EOD)
- 손절 발생 시 당일 정지
  - 손절 시 daily_stop_triggered = True
  - daily_stop_triggered = True인 당일은 신규 진입 금지
- WEEKLY는 완전히 비활성화

완료 기준
- DAILY가 하루 단위로 자동 실행되고 아래가 모두 지켜짐
  - 1회 진입 제한(daily_entry_taken)
  - TP/SL/EOD 준수
  - 손절 후 당일 정지(daily_stop_triggered)
  - 1포지션 유지(position_state)

---

## Day 5 — WEEKLY 전략 + weekly_mode 전환(1W ↔ 2_3W)
목표
- WEEKLY를 “조건 있을 때만” 진입하도록 구현하고,
  시장 상태에 따라 weekly_mode를 자동 선택

할 일
- weekly_mode 선택 함수 구현
  - weekly_mode_switch_score 계산
  - weekly_mode_switch_score >= WEEKLY_MODE_SWITCH_SCORE_THRESHOLD 이면 weekly_mode = 2_3W
  - 아니면 weekly_mode = 1W
- WEEKLY 신호 평가(H1 완성봉 기준)
  - bb_reentry_h1 / macd_recover_h1 / vol_confirm_h1 계산
  - weekly_signal_h1 = AND
- WEEKLY 진입(M5 확인 후)
  - weekly_signal_h1 True “이후”에만 진입 가능
  - entry_window_minutes(기본 120분) 내 진입만 허용
  - M5에서 close_5m(now) > max(high_5m[-1..-L]) 조건 충족 시 진입
  - 진입 시 position_state = WEEKLY
- 모드별 청산 규칙 구현
  - TP/SL
  - 시간손절(Time stop, 영업일 기준)
- 조기 청산은 기본 OFF 유지
  - ENABLE_EARLY_EXIT_WEEKLY = False

완료 기준
- WEEKLY 진입이 weekly_signal_h1 True일 때만 발생
- 모드별 TP/SL/시간손절 준수
- weekly_mode_switch_score 및 충족 조건 목록이 로그에 남음
- 1포지션 정책과 daily_stop_triggered 정책이 WEEKLY에서도 지켜짐

---

## 실전 전환 전 체크(권장)
- 모의투자에서 최소 1-2주 이상 로그 검증
- 아래 항목이 완벽히 지켜지는지 확인
  - 중복 주문 없음
  - 손절 후 당일 정지(daily_stop_triggered)
  - 1포지션 유지(position_state)
  - weekly_signal_h1의 H1 완성봉 기준 준수
- 실전은 소액(500,000원 고정)으로 시작
