# Auto Trading Strategy — KIS (Final)

이 문서는 사람이 읽는 전략 설명서다.  
정확한 구현 규격/수치/변수명은 SPEC.md와 src/strategy_config.py를 따른다.  
통과 조건(테스트)은 ACCEPTANCE.md를 따른다.

---

## 1. 목적
- 적립식 장기투자(메인)는 유지한다.
- 자동매매는 소액(500,000원)으로 저빈도 보조수익을 만든다.
- 자동매매 수익은 적립식 투자금에 보탠다(개념적 규칙).

---

## 2. 운영 원칙(최우선)
- 운용금: 500,000원 고정
- 손실 보전(추가 입금) 금지
- 물타기 금지
- 레버리지/미수/옵션 금지
- 저빈도 유지
- 동시에 1포지션만 허용

---

## 3. 전략 구성(2개)

### 3.1 전략 A — 장 초반 변동성 돌파 (DAILY MAIN)
- 매일 1회 시도
- 오프닝 레인지 상단 돌파 시 1회 진입
- 당일 청산(오버나잇 금지)

### 3.2 전략 B — 볼린저 밴드 + MACD + 거래량 (WEEKLY OPTIONAL)
- 기회가 있을 때만 진입(주 단위)
- 기본 모드: weekly_mode = 1W (최대 5영업일 보유)
- 확장 모드: weekly_mode = 2_3W (조건 충족 시에만, 최대 10영업일 보유)
- 신호 판단: H1(60분봉) 완성봉 기준
- 진입 타이밍: M5(5분봉) 확인 후 진입

---

## 4. 리스크/포지션 정책

### 4.1 1포지션 정책
- position_state가 NONE이 아닐 때 신규 진입 금지
- DAILY와 WEEKLY 동시 보유 금지

### 4.2 손절 후 당일 정지
- 손절 발생 시 daily_stop_triggered = True
- daily_stop_triggered = True인 당일에는 신규 진입 금지(DAILY/WEEKLY 모두)

### 4.3 주문/체결 동기화(중복 주문 방지)
- 주문 후 반드시 미체결 조회 → 체결 확인 → 잔고 확인 순서로 동기화
- 주문번호/원주문번호 저장으로 중복 주문 방지

---

## 5. 전략 A(DAILY) 개요

### 5.1 타임프레임
- 오프닝 레인지: 장 시작 후 5~15분(고정값 선택)
- 트리거/체결: M5 기준

### 5.2 진입(롱 only)
- opening_high = 오프닝 레인지 구간의 고가
- 현재가가 opening_high 상향 돌파 시 1회 진입
- daily_entry_taken = True로 잠금(당일 1회 제한)
- (선택) 거래량 필터로 약한 돌파는 스킵

### 5.3 청산
- TP/SL은 strategy_config.py 값으로 고정
- TP 또는 SL 도달 시 즉시 청산
- 장 종료 전 포지션이 남아 있으면 강제 청산(EOD close)

---

## 6. 전략 B(WEEKLY) 개요

### 6.1 타임프레임(3레이어)
- 환경 판단: D1(일봉), 2_3W 모드에서는 W1(주봉)+D1
- 신호 판단: H1(완성봉)
- 진입 타이밍: M5

### 6.2 진입 신호(H1)
- weekly_signal_h1 = bb_reentry_h1 AND macd_recover_h1 AND vol_confirm_h1
- 신호는 H1 완성봉에서만 평가한다.
- 구체 조건/수식은 SPEC.md를 따른다.

### 6.3 진입 타이밍(M5)
- H1에서 weekly_signal_h1 = True인 “신호봉 마감 이후”에만 진입 허용
- 신호봉 마감 이후 WEEKLY_ENTRY_WINDOW_MINUTES 이내만 유효
- M5에서 최근 L개 고가 돌파 시 진입(권장)

### 6.4 청산(모드별)
- weekly_mode = 1W
  - TP/SL + 시간손절 5영업일
- weekly_mode = 2_3W
  - TP/SL + 시간손절 10영업일
- 수치는 strategy_config.py를 따른다.
- 조기 청산은 기본 OFF(ENABLE_EARLY_EXIT_WEEKLY=False)

---

## 7. 주간 모드 전환(1W ↔ 2_3W)

### 7.1 기본 원칙
- 기본은 weekly_mode = 1W
- 조건 충족 시에만 weekly_mode = 2_3W
- 두 모드 동시 사용 금지

### 7.2 전환 규칙(점수 기반)
- weekly_mode_switch_score >= WEEKLY_MODE_SWITCH_SCORE_THRESHOLD 이면 2_3W
- 아니면 1W
- 조건/점수 정의는 SPEC.md를 따른다.

---

## 8. 로깅(필수)
- 모든 신호/진입/청산 이벤트를 logs에 남긴다.
  - DAILY: opening_high, trigger, 진입/청산 사유(TP/SL/EOD)
  - WEEKLY: bb_reentry_h1/macd_recover_h1/vol_confirm_h1 True/False, 진입/청산 사유(TP/SL/TIME/EARLY_EXIT), weekly_mode
  - 모드 전환: weekly_mode_switch_score 및 충족 조건 목록
- 키/토큰/시크릿은 로그에 절대 출력하지 않는다.
