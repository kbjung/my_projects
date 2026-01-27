# SPEC (Auto Trading) — KIS

목적
- 적립식 장기투자(메인)는 유지한다.
- 자동매매는 소액(500,000원)으로 저빈도 보조수익을 만든다.
- 자동매매 수익은 적립식 투자금에 보탠다(개념적 규칙).

0. 공통 운영 원칙
- 운용금: 500,000원 고정
- 추가 입금(손실 보전) 금지
- 물타기 금지
- 레버리지/미수/옵션 금지
- 거래 빈도는 매우 낮게 유지
- 동시에 1포지션만 허용

1. 상태 변수(필수)
- capital_fixed_krw: 500000
- equity_krw: 현재 평가금액
- position_state: NONE | DAILY | WEEKLY
- symbol_in_position: 포지션 보유 종목
- entry_price: 진입가
- entry_time: 진입 시각(타임스탬프)
- entry_date: 진입 일자(YYYY-MM-DD)
- daily_entry_taken: bool (DAILY 당일 진입 1회 잠금)
- daily_stop_triggered: bool (당일 손절 발생 후 거래 정지 플래그)
- weekly_mode: 1W | 2_3W
- weekly_position_open: bool
- weekly_days_held: int (보유 영업일 수)

2. 절대 규칙(안전장치)
2.1 손절 후 당일 정지
- daily_stop_triggered == True이면 당일 신규 진입 금지(DAILY/WEEKLY 모두)

2.2 1포지션 정책
- position_state != NONE 이면 신규 진입 금지

2.3 주문 동기화(중복 주문 방지)
- 주문 후 반드시 미체결 조회 → 체결 확인 → 잔고 확인
- 주문번호/원주문번호 저장으로 중복 주문 방지

3. 전략 A: 장 초반 변동성 돌파 (DAILY MAIN)
3.1 목표
- 하루 1회 시도(트리거 없으면 거래 없음)
- 당일 청산(오버나잇 금지)

3.2 시간/타임프레임
- 오프닝 레인지: 장 시작 후 5~15분(고정값 선택)
- 판단/트리거: M5

3.3 진입 조건(롱 only)
- opening_high = 오프닝 레인지 구간의 고가
- last_price > opening_high 이면 1회 진입
- 진입 시 daily_entry_taken = True
- (선택) 볼륨 필터:
  - 현재 M5 거래량 >= 최근 N개 M5 거래량 평균

3.4 청산 조건
- TP/SL: strategy_config.py 기준
- TP 또는 SL 도달 시 즉시 청산
- 장 종료 전 포지션이 남아 있으면 강제 청산(EOD close)

4. 전략 B: 볼린저 + MACD + 거래량 (WEEKLY OPTIONAL)
4.1 목표
- weekly_mode = 1W: 최대 5영업일 보유
- weekly_mode = 2_3W: 최대 10영업일 보유
- 기회가 있을 때만 진입(주 단위)

4.2 타임프레임
- 환경 판단: D1(일봉), 2_3W에서는 W1(주봉)+D1
- 신호 판단: H1(60분봉) 완성봉 고정
- 진입 타이밍: M5(5분봉)

4.3 지표 계산 정의 (H1 완성봉 기준)
4.3.1 볼린저 밴드 (SMA 기반)
- mid[t] = SMA(close, N)[t]
- sd[t] = STD(close, N)[t]
- upper[t] = mid[t] + K * sd[t]
- lower[t] = mid[t] - K * sd[t]

모드별 파라미터
- 1W: N=20, K=2.0
- 2_3W: N=35, K=2.2

4.3.2 MACD (EMA 기반)
- ema_fast[t] = EMA(close, fast)[t]
- ema_slow[t] = EMA(close, slow)[t]
- macd[t] = ema_fast[t] - ema_slow[t]
- signal[t] = EMA(macd, macd_signal_period)[t]
- hist[t] = macd[t] - signal[t]

모드별 파라미터
- 1W: fast=12, slow=26, macd_signal_period=9
- 2_3W: fast=19, slow=39, macd_signal_period=9

4.3.3 거래량 평균
- vol[t] = H1 거래량
- vol_ma[t] = SMA(vol, V)[t]

모드별 파라미터
- 1W: V=10
- 2_3W: V=15

4.4 엔트리 신호 정의 (H1) — 3조건 AND
- bb_reentry_h1[t], macd_recover_h1[t], vol_confirm_h1[t]
- weekly_signal_h1[t] = bb_reentry_h1[t] AND macd_recover_h1[t] AND vol_confirm_h1[t]
- 신호 평가는 반드시 H1 완성봉에서만 수행한다.

4.4.1 bb_reentry_h1 (기본 A안)
A안(엄격, 기본)
- close[t-1] <= lower[t-1]
- close[t] > lower[t]
→ bb_reentry_h1[t] = True

B안(완화, 선택)
- 최근 3봉 중 최소 1봉에서 low[k] <= lower[k] (k in {t-1,t-2,t-3})
- close[t] > lower[t]
→ bb_reentry_h1[t] = True

4.4.2 macd_recover_h1 (연속 2봉 hist 증가 + 추가조건)
필수
- hist[t] < 0
- hist[t] > hist[t-1]
- hist[t-1] > hist[t-2]
→ hist_up_2 = True

추가(둘 중 하나)
- macd[t] >= signal[t]
  또는
- macd[t] > macd[t-1]

권장 최종 정의
- macd_recover_h1[t] = hist_up_2 AND (macd[t] >= signal[t] OR macd[t] > macd[t-1])

4.4.3 vol_confirm_h1
- vol[t] >= vol_ma[t] * vol_factor

모드별 vol_factor
- 1W: 1.05
- 2_3W: 1.10

뉴스성 폭증 필터(옵션)
- vol_spike_filter_enabled == True이면:
  - vol[t] <= vol_ma[t] * vol_max_spike
- vol_max_spike: 3.0

4.4.4 추가 보수 필터(옵션)
- weekly_require_signal_candle_up == True이면:
  - close[t] > close[t-1] 일 때만 weekly_signal_h1 True로 인정

4.5 진입 타이밍 (M5)
- H1 신호봉 마감 이후에만 진입 가능
- 신호봉 마감 이후 entry_window_minutes 이내만 유효(기본 120분)
- 윈도우 내 진입 조건:
  - close_5m(now) > max(high_5m[-1..-L])
  - L = entry_5m_breakout_lookback (기본 3)

4.6 청산 조건(모드별)
- weekly_mode = 1W
  - TP/SL/시간손절: strategy_config.py 값
  - 시간손절: 5 영업일
- weekly_mode = 2_3W
  - TP/SL/시간손절: strategy_config.py 값
  - 시간손절: 10 영업일

공통
- TP/SL 충족 시 즉시 청산
- 시간손절은 영업일 기준으로 카운트

4.7 조기 청산(옵션, 기본 OFF)
- enable_early_exit_weekly == True일 때만 사용
- hist[t] < hist[t-1]
- close[t] < mid[t]
- close[t] <= close[t-1]
→ early_exit = True → 즉시 청산

5. weekly_mode 전환(1W ↔ 2_3W)
5.1 원칙
- 기본은 weekly_mode = 1W
- 조건 충족 시에만 weekly_mode = 2_3W
- 동시 모드 사용 금지

5.2 전환 조건(4개 중 3개 이상)
- 조건 1: 지수(D1) MACD hist가 바닥권에서 상승 전환
- 조건 2: 지수(D1) 가격 > MA20 AND MA5 > MA20
- 조건 3: 변동성 완화(예: ATR% 하락)
- 조건 4: 최근 2주간 DAILY 손절률 >= 50%

- weekly_mode_switch_score = 조건 충족 개수
- weekly_mode_switch_score >= weekly_mode_switch_score_threshold 이면 2_3W
- 아니면 1W

6. 로깅(필수)
- 모든 신호/진입/청산 이벤트는 logs에 기록
  - DAILY: opening_high, trigger, TP/SL/EOD 사유
  - WEEKLY: bb_reentry_h1/macd_recover_h1/vol_confirm_h1 True/False, TP/SL/TIME/EARLY_EXIT 사유, weekly_mode
  - 모드 전환: weekly_mode_switch_score 및 충족 조건 목록
- 키/토큰/시크릿은 로그에 절대 출력하지 않는다.
