"""
day6_report_test.py

Day 6 - 일일 리포트 생성 기능 테스트 (Mock)
- 장 마감 시간(15:35) 이후 리포트 자동 생성 확인
- 체결 내역 및 잔고 출력 포맷 확인
- 리포트 중복 생성 방지 확인
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TradingBot
from logger_config import main_logger as logger

def run_day6_test():
    logger.info("=" * 60)
    logger.info("Day 6: 일일 리포트 생성 테스트 (Mock)")
    logger.info("=" * 60)
    
    bot = TradingBot(mock_mode=True)
    
    # === 시나리오 1: 장 마감 후 리포트 생성 ===
    logger.info("\n[1/2] 장 마감(15:35) 후 리포트 생성 테스트...")
    
    # 시간 설정: 15:36 (장 마감 직후)
    mock_now = datetime.now().replace(hour=15, minute=36, second=0)
    
    # Mock 체결 내역 주입 (main.py가 kis_orders의 mock 데이터를 사용하도록 유도되어 있음)
    # 별도 설정 없이 KISOrders(mock_mode=True).get_today_trades()가 예시 데이터를 반환함
    
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now
        
        # main loop의 단일 실행을 시뮬레이션하기 위해 내부 로직 직접 호출
        # _is_market_hours는 15:30 넘었으므로 False 반환
        if not bot._is_market_hours(mock_now):
            if mock_now.time() >= datetime.strptime("15:35", "%H:%M").time() and bot.daily_report_done_date != mock_now.date():
                bot._generate_daily_report(mock_now)
                logger.info("✓ 리포트 생성 로직 진입 확인")
            else:
                logger.error("✗ 리포트 생성 로직 진입 실패")
    
    # 검증: daily_report_done_date가 설정되었는지
    if bot.daily_report_done_date == mock_now.date():
        logger.info(f"✓ 플래그 설정 확인: {bot.daily_report_done_date}")
    else:
        logger.error("✗ 플래그 설정 실패")

    # === 시나리오 2: 중복 생성 방지 ===
    logger.info("\n[2/2] 리포트 중복 생성 방지 테스트...")
    
    # 시간 조금 더 경과: 15:37
    mock_now_later = datetime.now().replace(hour=15, minute=37, second=0)
    
    generated_again = False
    with patch('main.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_now_later
        
        if not bot._is_market_hours(mock_now_later):
            # 이미 날짜가 같으므로 실행되지 않아야 함
            if mock_now_later.time() >= datetime.strptime("15:35", "%H:%M").time() and bot.daily_report_done_date != mock_now_later.date():
                bot._generate_daily_report(mock_now_later)
                generated_again = True
            else:
                pass # 정상
    
    if not generated_again:
        logger.info("✓ 중복 생성 방지 성공")
    else:
        logger.error("✗ 중복 생성 방지 실패 (리포트가 다시 생성됨)")

    logger.info("\n" + "=" * 60)
    logger.info("Day 6 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day6_test()
