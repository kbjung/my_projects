"""
day4_daily_automation_test.py

Day 4 — DAILY 전략 자동화 테스트 (Mock 환경)
- 오프닝 레인지 계산 확인
- 돌파 진입 자동 실행 확인
- 청산(EOD/TP) 자동 실행 확인
- 일일 제한(1회 진입) 확인
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TradingBot
from logger_config import main_logger as logger

def run_day4_test():
    logger.info("=" * 60)
    logger.info("Day 4: DAILY 전략 자동화 테스트 (Mock)")
    logger.info("=" * 60)
    
    # 봇 인스턴스 생성 (Mock 모드)
    # 주의: 내부 컴포넌트들을 테스트 목적에 맞게 조작해야 함
    bot = TradingBot(mock_mode=True)
    
    # 테스트용 데이터 설정
    symbol = "005930"
    
    # === 시나리오 1: 장 시작 ~ 오프닝 레인지 계산 ===
    logger.info("\n[1/4] 장 시작 및 오프닝 레인지 계산 테스트...")
    
    # 시간 조작: 09:11 (오프닝 레인지 10분 경과 후)
    mock_now = datetime.now().replace(hour=9, minute=11, second=0)
    
    # Mock M5 캔들 설정 (고가 50000원 가정)
    import pandas as pd
    m5_data = pd.DataFrame({
        'datetime': [mock_now - timedelta(minutes=5)], # 09:06
        'open': [49000], 'high': [50000], 'low': [48000], 'close': [49500], 'volume': [1000]
    })
    
    # 봇의 상태/데이터 강제 주입
    bot.marketdata.get_candles = MagicMock(return_value=m5_data)
    bot.marketdata.get_current_price = MagicMock(return_value=49500)
    
    # _update_market_data 실행
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        bot._update_market_data()
        
    # 검증
    if bot.daily_strategy.opening_high == 50000:
        logger.info(f"✓ 오프닝 레인지 계산 성공: {bot.daily_strategy.opening_high}")
    else:
        logger.error(f"✗ 오프닝 레인지 계산 실패: {bot.daily_strategy.opening_high}")
        return

    # === 시나리오 2: 돌파 진입 ===
    logger.info("\n[2/4] 돌파 진입 자동화 테스트...")
    
    # 시간: 09:30
    mock_now = datetime.now().replace(hour=9, minute=30, second=0)
    
    # 현재가: 50100 (돌파!)
    bot.marketdata.get_current_price = MagicMock(return_value=50100)
    
    # _check_entry_conditions 실행
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        bot._check_daily_entry(mock_now)
        
    # 검증
    time.sleep(1) # 비동기 처리 여유 (여기선 동기지만 안전하게)
    state = bot.state.get_position_state()
    daily_taken = bot.state.get_daily_entry_taken()
    
    if state == "DAILY" and daily_taken:
        entry_price = bot.state.get_position_info()["entry_price"]
        logger.info(f"✓ 진입 성공: 상태={state}, 진입가={entry_price}")
    else:
        logger.error(f"✗ 진입 실패: 상태={state}")
        return

    # === 시나리오 3: 1회 진입 제한 확인 ===
    logger.info("\n[3/4] 1회 진입 제한(Daily Entry Taken) 테스트...")
    
    # 가격 더 상승: 50200
    bot.marketdata.get_current_price = MagicMock(return_value=50200)
    
    # 주문 실행 횟수 추적을 위해 execute_buy_with_sync 모킹
    bot.order_sync.execute_buy_with_sync = MagicMock()
    
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        bot._check_daily_entry(mock_now)
        
    if bot.order_sync.execute_buy_with_sync.call_count == 0:
        logger.info("✓ 중복 진입 시도 차단 확인")
    else:
        logger.error("✗ 중복 진입 시도 발생 (실패)")

    # === 시나리오 4: 청산 (TP) ===
    logger.info("\n[4/4] 청산(TP) 자동화 테스트...")
    
    # 진입가 50100, TP +0.8% = 50500.8
    # 현재가 급등: 51000
    bot.marketdata.get_current_price = MagicMock(return_value=51000)
    
    # get_position 모킹 추가 (청산 시 포지션 수량 조회 필요)
    bot.orders.get_position = MagicMock(return_value={
        "symbol": "005930",
        "quantity": 9,
        "average_price": 50000
    })
    
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        bot._check_exit_conditions(mock_now)
        
    # 검증
    state = bot.state.get_position_state()
    if state == "NONE":
        logger.info("✓ 청산 성공: 상태=NONE")
    else:
        logger.error(f"✗ 청산 실패: 상태={state}")

    logger.info("\n" + "=" * 60)
    logger.info("Day 4 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day4_test()
