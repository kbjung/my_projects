"""
trade_recorder.py

매매 기록(History) 관리 모듈
- 거래 내역을 CSV 파일로 영구 저장
- 추후 수익률 분석 등을 위한 데이터셋 축적
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from logger_config import get_logger

logger = get_logger("recorder")

class TradeRecorder:
    """
    거래 내역 CSV 저장기
    """
    
    def __init__(self, file_path: str = "data/trades.csv"):
        self.file_path = Path(file_path)
        self._initialize_file()
        
    def _initialize_file(self):
        """파일이 없으면 헤더 작성"""
        if not self.file_path.exists():
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "symbol", "side", "position_type", # 기본 정보
                        "price", "quantity", "amount",                 # 체결 정보
                        "strategy_mode", "reason",                     # 전략 정보
                        "pnl_amount", "pnl_pct"                        # 청산 시 손익
                    ])
                logger.info(f"거래 기록 파일 생성 완료: {self.file_path}")
            except Exception as e:
                logger.error(f"거래 기록 파일 초기화 실패: {e}")

    def record_entry(
        self,
        symbol: str, 
        position_type: str, 
        price: float, 
        quantity: int,
        entry_time: datetime
    ):
        """진입 기록 저장"""
        row = [
            entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            "BUY",
            position_type,
            price,
            quantity,
            price * quantity,
            position_type, # strategy_mode와 position_type 동일하게 기록 (단순화)
            "Signal",      # 진입 사유는 보통 Signal
            "", ""         # 진입 시 PnL 없음
        ]
        self._append_row(row)

    def record_exit(
        self,
        symbol: str,
        position_type: str,
        price: float,
        quantity: int,
        exit_time: datetime,
        reason: str,
        entry_price: float
    ):
        """청산 기록 저장"""
        # 손익 계산
        total_exit_amt = price * quantity
        total_entry_amt = entry_price * quantity
        pnl_amount = total_exit_amt - total_entry_amt
        pnl_pct = (price - entry_price) / entry_price * 100 if entry_price else 0
        
        row = [
            exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            "SELL",
            position_type,
            price,
            quantity,
            total_exit_amt,
            position_type,
            reason,
            f"{pnl_amount:.0f}",
            f"{pnl_pct:.2f}"
        ]
        self._append_row(row)

    def _append_row(self, row: list):
        """CSV 행 추가"""
        try:
            with open(self.file_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"거래 기록 저장 실패: {e}")

    @staticmethod
    def infer_last_open_position_type(
        symbol: str,
        file_path: str = "data/trades.csv"
    ) -> Optional[str]:
        """
        거래 기록에서 마지막 미청산 포지션의 전략 타입 추론
        - 마지막 거래가 BUY이면 해당 position_type 반환
        - 마지막 거래가 SELL이면 None 반환
        """
        path = Path(file_path)
        if not path.exists():
            return None

        last_row = None
        try:
            with open(path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("symbol") == symbol:
                        last_row = row
        except Exception as e:
            logger.error(f"거래 기록 조회 실패: {e}")
            return None

        if not last_row:
            return None

        if last_row.get("side") == "BUY":
            return last_row.get("position_type")

        return None
