# ACCEPTANCE (Must Pass)

목표
- 코드가 SPEC.md의 규칙을 지키는지 검증하기 위한 통과 조건 목록

A. 공통 안전장치
A-1. 손절 후 당일 정지
- 어떤 전략에서든 손절이 발생하면 daily_stop_triggered가 True가 된다.
- daily_stop_triggered가 True인 당일에는 신규 진입이 절대 발생하지 않는다(DAILY/WEEKLY 모두).

A-2. 동시 포지션 금지
- position_state가 DAILY 또는 WEEKLY일 때, 신규 진입은 절대 발생하지 않는다.
- 포지션은 항상 1개 이하이다.

A-3. 물타기 금지
- 동일 종목 추가매수 로직이 존재하지 않는다.
- 포지션 보유 중에는 수량 증가가 발생하지 않는다.

A-4. 주문 동기화
- 주문 후 미체결 조회 → 체결 확인 → 잔고 확인이 수행되어 상태가 일관되게 갱신된다.
- 중복 주문이 발생하지 않는다(주문번호/원주문번호 추적).

B. DAILY(변동성 돌파) 전략
B-1. 오프닝 레인지 계산
- 장 시작 후 5~15분 구간에서 opening_high가 계산된다.

B-2. 1회/일 원칙
- 하루에 DAILY 진입은 최대 1회만 발생한다(daily_entry_taken이 True로 잠금).

B-3. TP/SL 준수
- 진입 후 TP 또는 SL 도달 시 즉시 청산된다.
- TP/SL 값은 strategy_config.py의 DAILY_TP_PCT, DAILY_SL_PCT를 사용한다.

B-4. 당일 청산(EOD close)
- 장 종료 시 DAILY 포지션은 반드시 청산된다(오버나잇 금지).

C. WEEKLY(볼린저+MACD+거래량) 전략
C-0. 신호는 H1 완성봉 기준
- weekly_signal_h1은 H1 완성봉 기준으로만 평가한다.
- 미완성 H1 봉으로는 weekly_signal_h1이 True가 될 수 없다.

C-1. 3조건 충족 없으면 진입 금지
- bb_reentry_h1, macd_recover_h1, vol_confirm_h1 3개가 모두 True가 아니면 WEEKLY 진입이 발생하지 않는다.

C-2. bb_reentry_h1 (A안) 준수
- A안 사용 시:
  - close[t-1] <= lower[t-1]
  - close[t] > lower[t]
  를 만족하지 않으면 bb_reentry_h1은 True가 될 수 없다.

C-3. macd_recover_h1 준수
- hist[t] < 0 이어야 한다.
- hist[t] > hist[t-1] AND hist[t-1] > hist[t-2] (연속 2봉 증가) 없이 macd_recover_h1은 True가 될 수 없다.
- 추가 조건(macd[t] >= signal[t] OR macd[t] > macd[t-1])을 만족해야 한다.

C-4. vol_confirm_h1 준수
- vol[t] >= vol_ma[t] * vol_factor 를 만족해야 한다.
- vol_spike_filter_enabled == True인 경우:
  - vol[t] <= vol_ma[t] * vol_max_spike 를 만족해야 한다.

C-5. M5 진입 윈도우 준수
- H1 신호봉 마감 이후 entry_window_minutes 안에만 진입이 가능하다.
- 윈도우가 지나면 해당 신호는 폐기되며 진입이 발생하지 않는다.

C-6. M5 진입 조건 준수
- close_5m(now) > max(high_5m[-1..-L]) 조건이 True일 때만 진입한다.
- L은 entry_5m_breakout_lookback 값이다.

C-7. 모드별 TP/SL/시간손절 준수
- weekly_mode가 1W이면:
  - TP는 WEEKLY_TP_PCT_1W
  - SL은 WEEKLY_SL_PCT_1W
  - 시간손절은 WEEKLY_TIME_STOP_DAYS_1W
- weekly_mode가 2_3W이면:
  - TP는 WEEKLY_TP_PCT_2_3W
  - SL은 WEEKLY_SL_PCT_2_3W
  - 시간손절은 WEEKLY_TIME_STOP_DAYS_2_3W

C-8. 시간손절(Time stop)
- 시간손절 기준 영업일을 초과하면 포지션이 청산된다.
- 시간손절 청산 사유가 로그에 기록된다.

C-9. 조기 청산(옵션)
- enable_early_exit_weekly == True일 때만 조기청산이 발생할 수 있다.
- 비활성(enable_early_exit_weekly == False) 상태에서는 조기청산이 발생하지 않는다.

D. weekly_mode 전환(1W ↔ 2_3W)
D-1. 기본은 1W
- 조건이 충족되지 않으면 weekly_mode는 항상 1W이다.

D-2. 점수 기반 전환
- weekly_mode_switch_score >= weekly_mode_switch_score_threshold 일 때만 weekly_mode가 2_3W가 된다.
- 점수 및 충족 조건 목록이 로그에 남는다.

E. 로깅/재현성
E-1. 모든 진입/청산 이벤트는 로그에 남는다.
- 진입: 전략명, 시간, 가격, 수량, 근거(조건 True/False)
- 청산: 전략명, 시간, 가격, 수익률, 사유(TP/SL/EOD/TIME/EARLY_EXIT)

E-2. 키/토큰 비노출
- 로그/에러 출력에 AppKey/AppSecret/AccessToken이 포함되지 않는다.
