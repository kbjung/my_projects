"""
day10_ui_test.py

Day 10 - UI/UX 개선 테스트 (Mock)
- 시작 시 계좌 요약 표 형식 출력 확인
- 일일 리포트 체결 내역 및 잔고 표 형식 출력 확인
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import TradingBot
from logger_config import main_logger as logger

class Day10UITest(unittest.TestCase):
    def setUp(self):
        self.bot = TradingBot(mock_mode=True)
        # Mock Orders
        self.bot.orders = MagicMock()
        
    def test_startup_summary_format(self):
        print("\n" + "=" * 60)
        print("Test 1: Startup Summary Formatting")
        print("=" * 60)
        
        # Mock Balance with Positions
        self.bot.orders.get_balance.return_value = {
            "cash": 500000000.0,
            "total_asset": 500150000.0,
            "positions": [
                {
                    "symbol": "005930",
                    "quantity": 10,
                    "avg_price": 50000.0,
                    "current_price": 65000.0,
                    "eval_amount": 650000.0,
                    "profit_loss": 150000.0
                }
            ]
        }
        
        # Execute
        self.bot._print_startup_summary()
        
    def test_daily_report_format(self):
        print("\n" + "=" * 60)
        print("Test 2: Daily Report Formatting")
        print("=" * 60)
        
        # Mock Trades
        self.bot.orders.get_today_trades.return_value = [
            {
                "time": "09:30:00",
                "symbol": "005930",
                "side": "buy",
                "qty": 10,
                "price": 50000.0,
                "total_price": 500000.0
            },
            {
                "time": "15:00:00",
                "symbol": "005930",
                "side": "sell",
                "qty": 5,
                "price": 55000.0,
                "total_price": 275000.0
            }
        ]
        
        # Mock Balance (Same as above)
        self.bot.orders.get_balance.return_value = {
            "cash": 500000000.0,
            "total_asset": 500150000.0,
            "positions": [
                {
                    "symbol": "005930",
                    "quantity": 5, # 5 left
                    "avg_price": 50000.0,
                    "current_price": 60000.0,
                    "eval_amount": 300000.0,
                    "profit_loss": 50000.0
                }
            ]
        }
        
        # Execute
        self.bot._generate_daily_report(datetime.now())

if __name__ == "__main__":
    unittest.main()
