"""
day2_signal_test.py

Day 2 — 데이터 파이프라인 + 지표 계산 + 신호 생성 테스트
(주문 금지, 신호 논거 기록 중심)
"""

import sys
from pathlib import Path
from datetime import datetime

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kis_marketdata import KISMarketData
from indicators import add_all_indicators
from strategy_daily import DailyStrategy
from strategy_weekly import WeeklyStrategy
from logger_config import main_logger as logger, strategy_logger


def run_day2_test():
    logger.info("=" * 60)
    logger.info("Day 2: 데이터 파이프라인 및 신호 생성 테스트 시작")
    logger.info("=" * 60)

    symbol = "005930"  # 삼성전자
    marketdata = KISMarketData(mock_mode=True)
    daily_strat = DailyStrategy()
    weekly_strat = WeeklyStrategy(mode="1W")

    try:
        # 1. 데이터 수집 (M5, H1, D1)
        logger.info(f"\n[1/4] 데이터 수집 중... ({symbol})")
        m5_df = marketdata.get_candles(symbol, "M5", count=100)
        h1_df = marketdata.get_candles(symbol, "H1", count=100)
        d1_df = marketdata.get_candles(symbol, "D1", count=100)

        if m5_df is None or h1_df is None or d1_df is None:
            logger.error("데이터 수집 실패")
            return

        logger.info(f"수집 완료: M5({len(m5_df)}), H1({len(h1_df)}), D1({len(d1_df)})")

        # 2. 지표 계산 (H1 중심)
        logger.info("\n[2/4] 지표 계산 중 (H1 중심)...")
        h1_with_indicators = add_all_indicators(h1_df, mode="1W")
        
        # 지표 샘플 확인
        last_row = h1_with_indicators.iloc[-1]
        logger.info(f"H1 지표 샘플 (마지막 봉):")
        logger.info(f" - BB: Mid={last_row['bb_mid']:.2f}, Lower={last_row['bb_lower']:.2f}")
        logger.info(f" - MACD: Hist={last_row['macd_hist']:.4f}, Signal={last_row['macd_signal']:.4f}")
        logger.info(f" - Vol MA: {last_row['vol_ma']:.0f}")

        # 3. DAILY 신호 생성 테스트
        logger.info("\n[3/4] DAILY 신호 검증...")
        market_open_time = m5_df.iloc[0]['datetime'].replace(hour=9, minute=0, second=0)
        daily_strat.calculate_opening_high(m5_df, market_open_time)
        
        current_price = m5_df.iloc[-1]['close']
        daily_signal = daily_strat.check_breakout_signal(current_price)
        logger.info(f"DAILY 신호 결과: {daily_signal} (현재가: {current_price}, opening_high: {daily_strat.opening_high})")

        # 4. WEEKLY 신호 검증 (H1 완성봉 기준)
        logger.info("\n[4/4] WEEKLY 신호 검증 (H1 완성봉)...")
        weekly_signal = weekly_strat.evaluate_h1_signal(h1_with_indicators, is_complete_candle=True)
        logger.info(f"WEEKLY 신호 결과: {weekly_signal}")

        # 5. 동일 입력 -> 동일 결과 재현성 확인
        logger.info("\n[5/4] 동일 입력 재현성(Reproducibility) 확인...")
        weekly_strat_2 = WeeklyStrategy(mode="1W")
        weekly_signal_2 = weekly_strat_2.evaluate_h1_signal(h1_with_indicators, is_complete_candle=True)
        
        if weekly_signal == weekly_signal_2:
            logger.info("✓ 재현성 확인 성공: 동일한 데이터에 대해 동일한 신호 생성됨.")
        else:
            logger.error("✗ 재현성 확인 실패: 동일한 데이터에 대해 다른 신호가 생성됨!")

        # 결과 저장
        # tests/output 디렉토리에 저장 (없으면 생성)
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"{symbol}_H1_indicators.csv"
        h1_with_indicators.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n지표 결과 저장 완료: {output_file}")

    except Exception as e:
        logger.error(f"Day 2 테스트 중 오류 발생: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)
    logger.info("Day 2 테스트 종료")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_day2_test()
