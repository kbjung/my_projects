"""
day7_ux_test.py

Day 7 - UX 개선 (출력 포맷) 테스트 (Mock)
- 봇 시작 시 계좌 잔고 요약 출력 확인
- 매수/매도 시 종목명 포함 포맷 확인
- 루프 로그 최소화 (터미널이 깨끗한지 확인용)
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

def run_day7_test():
    logger.info("=" * 60)
    logger.info("Day 7: UX 출력 개선 테스트 (Mock)")
    logger.info("=" * 60)
    
    bot = TradingBot(mock_mode=True)
    
    # === 시나리오 1: 시작 시 요약 출력 ===
    logger.info("\n[1/2] 봇 시작 및 계좌 요약 출력 테스트...")
    # start() 대신 _print_startup_summary 직접 호출하여 확인
    bot._print_startup_summary()

    # === 시나리오 2: 매매 로그 포맷 확인 ===
    logger.info("\n[2/2] 매매 로그 포맷 확인...")
    
    symbol = "005930"
    
    # 1) 매수 로그
    # _execute_entry 호출 (내부적으로 s_name 조회 및 로그 출력)
    mock_now = datetime.now()
    bot._execute_entry("DAILY", symbol, 50000, mock_now)
    
    time.sleep(1)
    
    # 2) 매도 로그
    # 포지션 모킹 필요
    bot.orders.get_position = MagicMock(return_value={
        "symbol": symbol, "quantity": 10, "average_price": 50000
    })
    
    bot._execute_exit(symbol, 51000, "TP")
    
    logger.info("\n" + "=" * 60)
    logger.info("Day 7 테스트 종료 (터미널 출력을 직접 확인하세요)")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day7_test()
