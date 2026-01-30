"""
day5_weekly_automation_test.py

Day 5 — WEEKLY 전략 및 모드 전환 테스트 (Mock 환경)
- 주간 모드 자동 전환 확인 (1W <-> 2_3W)
- 주간 신호(H1) 발생 시 자동 진입 확인
- 주간 포지션 청산(TP/SL/Time) 확인
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TradingBot
from logger_config import main_logger as logger

def create_mock_candles(count: int, start_price: float, trend: float = 0):
    prices = [start_price + (i * trend) + np.random.normal(0, 100) for i in range(count)]
    df = pd.DataFrame({
        'datetime': [datetime.now() - timedelta(hours=count-i) for i in range(count)],
        'open': prices,
        'high': [p + 200 for p in prices],
        'low': [p - 200 for p in prices],
        'close': prices,
        'volume': [100000] * count
    })
    return df

def run_day5_test():
    logger.info("=" * 60)
    logger.info("Day 5: WEEKLY 전략 및 모드 전환 테스트 (Mock)")
    logger.info("=" * 60)

    # 이전 테스트 상태 초기화
    state_path = Path(__file__).parent / "output" / "state.json"
    if state_path.exists():
        state_path.unlink()

    bot = TradingBot(mock_mode=True)
    symbol = "005930"
    
    # === 시나리오 1: 모드 전환 테스트 (1W -> 2_3W) ===
    logger.info("\n[1/3] 모드 전환 자동화 테스트 (1W -> 2_3W)...")
    
    # D1 캔들 생성: 상승 추세 (MA 정배열 유도)
    d1_data = create_mock_candles(50, 50000, trend=100)
    
    # 데이터 주입
    bot.marketdata.get_candles = MagicMock(return_value=d1_data)
    
    # 모드 스위처 강제 조작 (지표 계산 복잡성 회피)
    # select_mode가 ("2_3W", 3, [...])을 반환하도록 설정
    bot.mode_switcher.select_mode = MagicMock(return_value=("2_3W", 3, ["Mock 조건"]))
    
    # 실행
    bot._check_weekly_mode_switch()
    
    # 검증
    current_mode = bot.state.get_weekly_mode()
    if current_mode == "2_3W":
        logger.info(f"✓ 모드 전환 성공: {current_mode}")
    else:
        logger.error(f"✗ 모드 전환 실패: {current_mode}")
        return

    # === 시나리오 2: WEEKLY 진입 테스트 ===
    logger.info("\n[2/3] WEEKLY 진입 자동화 테스트...")
    
    # H1 데이터 주입 (신호 계산용)
    h1_data = create_mock_candles(100, 52000)
    bot.marketdata.get_candles = MagicMock(return_value=h1_data)
    bot.marketdata.get_current_price = MagicMock(return_value=52000)
    
    # 전략 신호 강제 True 설정 (evaluate_h1_signal)
    bot.weekly_strategy.evaluate_h1_signal = MagicMock(return_value=True)
    bot.weekly_strategy.select_complete_h1_candles = MagicMock(return_value=h1_data)
    bot.weekly_strategy.check_m5_entry_timing = MagicMock(return_value=True)
    
    # 시간 설정 (현재 시간)
    mock_now = datetime.now().replace(hour=10, minute=0)
    
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        # 진입 조건 체크
        bot._check_weekly_entry(mock_now)
        
    time.sleep(1)
    
    # 검증
    state = bot.state.get_position_state()
    if state == "WEEKLY":
        entry_price = bot.state.get_position_info()["entry_price"]
        logger.info(f"✓ 진입 성공: 상태={state}, 진입가={entry_price}")
    else:
        logger.error(f"✗ 진입 실패: 상태={state}")
        return

    # === 시나리오 3: WEEKLY 청산 테스트 (Time Stop) ===
    logger.info("\n[3/3] WEEKLY 청산(Time Stop) 테스트...")
    
    # 보유 기간 강제 변경 (10일 경과)
    # 현재 2_3W 모드이므로 max_days=10 (CONFIG.WEEKLY_TIME_STOP_DAYS_2_3W)
    # 확실한 청산을 위해 15일로 설정
    bot.state._state["weekly_days_held"] = 15

    # TP/SL이 아닌 TIME으로만 청산되도록 현재가를 진입가와 동일하게 고정
    entry_price = bot.state.get_position_info()["entry_price"] or 52000
    bot.marketdata.get_current_price = MagicMock(return_value=entry_price)

    # 포지션 정보 모킹 (수량/평단가 일치)
    capital = bot.state._state.get("capital_fixed_krw", 500000)
    quantity = int(capital / entry_price) if entry_price else 1
    bot.orders.get_position = MagicMock(return_value={
        "symbol": symbol, "quantity": quantity, "average_price": entry_price
    })
    
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        bot._check_exit_conditions(mock_now)
        
    time.sleep(1)
    
    # 검증
    state = bot.state.get_position_state()
    if state == "NONE":
        logger.info("✓ 청산 성공: 상태=NONE (Time Stop 동작)")
    else:
        logger.error(f"✗ 청산 실패: 상태={state}")

    logger.info("\n" + "=" * 60)
    logger.info("Day 5 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day5_test()
