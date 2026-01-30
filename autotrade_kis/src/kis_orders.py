"""
kis_orders.py

한국투자증권 API 주문 실행 및 추적 모듈
"""

import os
import requests
from typing import Optional, Literal, Dict, List, Tuple
from datetime import datetime

from kis_auth import get_auth
from logger_config import get_logger

logger = get_logger("orders")


class KISOrders:
    """
    주문 실행 및 추적 클래스
    
    기능:
    - 매수/매도 주문 발주
    - 주문 상태 조회
    - 포지션 조회
    - 잔고 조회
    - 주문 번호 추적
    - Mock 모드 지원
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Args:
            mock_mode: Mock 모드 사용 여부
        """
        self.auth = get_auth(mock_mode=mock_mode)
        self.mock_mode = self.auth.mock_mode
        self.base_url = self.auth.base_url
        # KIS_ACCOUNT_NO가 없으면 KIS_ACCOUNT 사용
        self.account_no = os.getenv("KIS_ACCOUNT_NO", os.getenv("KIS_ACCOUNT", ""))
        
        if not self.account_no:
            logger.error("계좌번호 설정 누락: .env의 KIS_ACCOUNT_NO 또는 KIS_ACCOUNT 확인 필요")
        self._order_numbers: List[str] = []
        
        # Mock 모드용 카운터
        self._mock_order_counter = 1000
    
    def _parse_account_no(self) -> Optional[Tuple[str, str]]:
        """계좌번호 파싱 (앞 8자리 / 뒤 2자리)"""
        acct = (self.account_no or "").strip()
        if not acct:
            logger.error("계좌번호 설정 누락: KIS_ACCOUNT_NO 또는 KIS_ACCOUNT 확인 필요")
            return None

        if "-" in acct:
            parts = acct.split("-")
        else:
            if len(acct) < 10:
                logger.error(f"계좌번호 형식 오류: {acct}")
                return None
            parts = [acct[:8], acct[8:]]

        if len(parts) != 2 or not parts[0] or not parts[1]:
            logger.error(f"계좌번호 파싱 실패: {acct}")
            return None

        return parts[0], parts[1]

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: Literal["market", "limit"] = "market"
    ) -> Optional[str]:
        """
        매수 주문
        """
        # Mock 모드라도 VTS 서버를 이용하므로 로컬 가짜 반환 로직 제거
        
        try:
            # 실제 API 호출 (VTS or Real)
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            account_parts = self._parse_account_no()
            if not account_parts:
                return None
            
            # TR ID 선택 (Mock vs Real)
            tr_id = "VTTC0802U" if self.mock_mode else "TTTC0802U"
            headers = self.auth.get_headers(tr_id=tr_id)
            
            body = {
                "CANO": account_parts[0],
                "ACNT_PRDT_CD": account_parts[1],
                "PDNO": symbol,
                "ORD_DVSN": "01" if order_type == "market" else "00",  # 01=시장가, 00=지정가
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(int(price)) if price else "0",
            }
            
            response = requests.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("rt_cd") == "0":
                order_no = data["output"]["ODNO"]
                self._order_numbers.append(order_no)
                logger.info(
                    f"매수 주문 성공: {symbol} | 수량={quantity} | "
                    f"가격={price} | 주문번호={order_no}"
                )
                return order_no
            else:
                logger.error(f"매수 주문 실패: {data.get('msg1', 'Unknown error')}")
                return None
        
        except Exception as e:
            logger.error(f"매수 주문 오류: {e}")
            return None
    
    def sell(
        self,
        symbol: str,
        quantity: int,
        price: Optional[float] = None,
        order_type: Literal["market", "limit"] = "market"
    ) -> Optional[str]:
        """
        매도 주문
        """
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            account_parts = self._parse_account_no()
            if not account_parts:
                return None
            
            tr_id = "VTTC0801U" if self.mock_mode else "TTTC0801U"
            headers = self.auth.get_headers(tr_id=tr_id)
            
            body = {
                "CANO": account_parts[0],
                "ACNT_PRDT_CD": account_parts[1],
                "PDNO": symbol,
                "ORD_DVSN": "01" if order_type == "market" else "00",
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(int(price)) if price else "0",
            }
            
            response = requests.post(url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("rt_cd") == "0":
                order_no = data["output"]["ODNO"]
                self._order_numbers.append(order_no)
                logger.info(
                    f"매도 주문 성공: {symbol} | 수량={quantity} | "
                    f"가격={price} | 주문번호={order_no}"
                )
                return order_no
            else:
                logger.error(f"매도 주문 실패: {data.get('msg1', 'Unknown error')}")
                return None
        
        except Exception as e:
            logger.error(f"매도 주문 오류: {e}")
            return None
    
    def get_order_status(self, order_no: str) -> Optional[Dict]:
        """
        주문 상태 조회
        """
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
            
            account_parts = self._parse_account_no()
            if not account_parts:
                return None
            
            tr_id = "VTTC8001R" if self.mock_mode else "TTTC8001R"
            headers = self.auth.get_headers(tr_id=tr_id)
            
            params = {
                "CANO": account_parts[0],
                "ACNT_PRDT_CD": account_parts[1],
                "INQR_STRT_DT": datetime.now().strftime("%Y%m%d"),
                "INQR_END_DT": datetime.now().strftime("%Y%m%d"),
                "SLL_BUY_DVSN_CD": "00",  # 00=전체
                "INQR_DVSN": "00",
                "PDNO": "",
                "CCLD_DVSN": "00",
                "ORD_GNO_BRNO": "",
                "ODNO": order_no,
                "INQR_DVSN_3": "00",
                "INQR_DVSN_1": "",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("rt_cd") == "0" and data.get("output1"):
                output = data["output1"][0]
                return {
                    "order_no": output["odno"],
                    "status": "filled" if output["ord_qty"] == output["tot_ccld_qty"] else "pending",
                    "filled_qty": int(output["tot_ccld_qty"]),
                    "filled_price": float(output["avg_prvs"])
                }
            else:
                logger.warning(f"주문 상태 조회 실패: {order_no}")
                return None
        
        except Exception as e:
            logger.error(f"주문 상태 조회 오류: {e}")
            return None
    
    def get_balance(self) -> Optional[Dict]:
        """
        잔고 조회
        """
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            account_parts = self._parse_account_no()
            if not account_parts:
                return None
            
            tr_id = "VTTC8434R" if self.mock_mode else "TTTC8434R"
            headers = self.auth.get_headers(tr_id=tr_id)
            
            params = {
                "CANO": account_parts[0],
                "ACNT_PRDT_CD": account_parts[1],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("rt_cd") == "0":
                output1 = data.get("output1", [])
                output2 = data.get("output2", [{}])[0]
                
                positions = []
                for item in output1:
                    if int(item["hldg_qty"]) > 0:
                        positions.append({
                            "symbol": item["pdno"],
                            "quantity": int(item["hldg_qty"]),
                            "avg_price": float(item["pchs_avg_pric"]),
                            "current_price": float(item["prpr"]),
                            "eval_amount": float(item["evlu_amt"]),
                            "profit_loss": float(item["evlu_pfls_amt"])
                        })
                
                return {
                    "cash": float(output2.get("dnca_tot_amt", 0)),
                    "total_asset": float(output2.get("tot_evlu_amt", 0)),
                    "positions": positions
                }
            else:
                logger.error(f"잔고 조회 실패: {data.get('msg1', 'Unknown error')}")
                return None
        
        except Exception as e:
            logger.error(f"잔고 조회 오류: {e}")
            return None
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        특정 종목 포지션 조회
        """
        balance = self.get_balance()
        if not balance:
            return None
        
        for pos in balance["positions"]:
            if pos["symbol"] == symbol:
                return pos
        
        return None

    def get_today_trades(self) -> List[Dict]:
        """
        당일 체결 내역 조회
        """
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
            
            account_parts = self._parse_account_no()
            if not account_parts:
                return []
            
            tr_id = "VTTC8001R" if self.mock_mode else "TTTC8001R"
            headers = self.auth.get_headers(tr_id=tr_id)
            
            params = {
                "CANO": account_parts[0],
                "ACNT_PRDT_CD": account_parts[1],
                "INQR_STRT_DT": datetime.now().strftime("%Y%m%d"),
                "INQR_END_DT": datetime.now().strftime("%Y%m%d"),
                "SLL_BUY_DVSN_CD": "00", # 전체
                "INQR_DVSN": "00",       # 역순
                "PDNO": "",
                "CCLD_DVSN": "01",       # 01=체결
                "ORD_GNO_BRNO": "",
                "ODNO": "",
                "INQR_DVSN_3": "00",
                "INQR_DVSN_1": "",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trades = []
            
            if data.get("rt_cd") == "0":
                for item in data.get("output1", []):
                    trades.append({
                        "order_no": item["odno"],
                        "time": item["ord_tmd"],
                        "symbol": item["pdno"],
                        "side": "buy" if item["sll_buy_dvsn_cd"] == "02" else "sell", # 02=매수, 01=매도
                        "qty": int(item["tot_ccld_qty"]),
                        "price": float(item["avg_prvs"]),
                        "total_price": float(item["tot_ccld_amt"])
                    })
            
            return trades
            
        except Exception as e:
            logger.error(f"당일 체결 내역 조회 실패: {e}")
            return []
