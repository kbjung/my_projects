"""
day8_csv_test.py

Day 8 - 거래 기록 CSV 저장 기능 테스트 (Mock)
- 진입 시 CSV에 매수 기록 저장 확인
- 청산 시 CSV에 매도 기록(수익률 포함) 저장 확인
- 파일 포맷 및 내용 검증
"""

import sys
import time
import csv
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TradingBot
from logger_config import main_logger as logger

def run_day8_test():
    logger.info("=" * 60)
    logger.info("Day 8: 거래 기록 CSV 저장 테스트 (Mock)")
    logger.info("=" * 60)
    
    # 테스트용 CSV 파일 경로 설정
    test_csv_path = Path(__file__).parent / "output" / "test_trades.csv"
    if test_csv_path.exists():
        test_csv_path.unlink() # 이전 테스트 파일 삭제
    
    # 봇 초기화 및 Recorder 경로 오버라이드
    # main.py의 TradingBot 내부에서 recorder 생성 시 경로를 주입할 수 없으므로,
    # 생성된 후 속성을 교체하거나 patch를 사용해야 함.
    # 여기서는 patch를 사용하여 recorder 생성 시 인자 변경을 유도하기보다,
    # bot.recorder 객체를 새 TradeRecorder(test_path)로 교체
    
    bot = TradingBot(mock_mode=True)
    
    from trade_recorder import TradeRecorder
    bot.recorder = TradeRecorder(file_path=str(test_csv_path)) # 테스트용 경로로 교체
    
    symbol = "005930"
    mock_now = datetime.now()
    
    # 1. 진입 기록 테스트
    logger.info("\n[1/2] 진입 기록(CSV) 테스트...")
    bot._execute_entry("DAILY", symbol, 50000, mock_now)
    
    time.sleep(0.5)
    
    # 파일 확인
    if not test_csv_path.exists():
        logger.error("✗ CSV 파일 생성 실패")
        return

    with open(test_csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
        
    # 헤더 + 1개 행
    if len(rows) < 2:
        logger.error(f"✗ CSV 기록 실패: 행 개수 부족 ({len(rows)})")
    else:
        last_row = rows[-1]
        # timestamp, symbol, side, position_type, price, qty ...
        # [0]        [1]     [2]   [3]            [4]    [5]
        if last_row[1] == symbol and last_row[2] == "BUY":
            logger.info("✓ 진입 기록 확인: BUY ROW 존재")
        else:
            logger.error(f"✗ 진입 기록 불일치: {last_row}")

    # 2. 청산 기록 테스트
    logger.info("\n[2/2] 청산 기록(CSV) 테스트...")
    
    # 포지션 정보 모킹 (청산 로직용)
    bot.orders.get_position = MagicMock(return_value={
        "symbol": symbol, "quantity": 10, "average_price": 50000
    })
    
    # 청산 실행 (TP +10%)
    bot._execute_exit(symbol, 55000, "TP")
    
    time.sleep(0.5)
    
    with open(test_csv_path, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    
    # 헤더 + 진입 + 청산 = 3개 행 예상
    if len(rows) < 3:
        logger.error(f"✗ CSV 기록 실패: 행 개수 부족 ({len(rows)})")
    else:
        last_row = rows[-1]
        # SELL 기록 확인
        if last_row[2] == "SELL" and last_row[8] == "TP":
            pnl_amt = last_row[9]
            pnl_pct = last_row[10]
            logger.info(f"✓ 청산 기록 확인: SELL ROW 존재 (PnL: {pnl_amt}원, 수익률: {pnl_pct}%)")
        else:
            logger.error(f"✗ 청산 기록 불일치: {last_row}")

    logger.info("\n" + "=" * 60)
    logger.info("Day 8 테스트 종료")
    logger.info("=" * 60)

if __name__ == "__main__":
    run_day8_test()
