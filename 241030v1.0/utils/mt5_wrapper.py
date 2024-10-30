import MetaTrader5 as mt5
from datetime import datetime
import time
from typing import Dict, List, Optional, Any, Union

class MT5Wrapper:
    """MT5 API 래퍼"""
    def __init__(self, logger=None):
        self.logger = logger
        self.max_retries = 3
        self.retry_delay = 1.0
        self.initialized = False
        
    def _log(self, message: str, level: str = 'info'):
        """로그 출력"""
        if self.logger:
            getattr(self.logger, level)(message)
        
    def initialize(self) -> bool:
        """MT5 초기화"""
        if self.initialized:
            return True
            
        retry_count = self.max_retries
        while retry_count > 0:
            if mt5.initialize():
                self.initialized = True
                self._log("MT5 연결 성공")
                return True
                
            self._log(f"MT5 연결 실패, 재시도... ({retry_count})", 'warning')
            time.sleep(self.retry_delay)
            retry_count -= 1
            
        self._log("MT5 연결 실패", 'error')
        return False
        
    def shutdown(self):
        """MT5 종료"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            self._log("MT5 연결 종료")
            
    def check_connection(self) -> bool:
        """연결 상태 확인"""
        if not self.initialized:
            return self.initialize()
        return True
        
    def get_server_time(self) -> Optional[float]:
        """서버 시간 조회"""
        if not self.check_connection():
            return None
            
        tick = mt5.symbol_info_tick("#USNDAQ100")
        if tick is None:
            self._log("서버 시간 조회 실패", 'error')
            return None
            
        return float(tick.time)
        
    def get_candles(self, symbol: str, timeframe: int, count: int) -> Optional[List[Dict]]:
        """봉 데이터 조회"""
        if not self.check_connection():
            return None
            
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            self._log(f"{symbol} 데이터 조회 실패", 'error')
            return None
            
        return rates
        
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """포지션 조회"""
        if not self.check_connection():
            return []
            
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            self._log(f"{symbol} 포지션 조회 실패", 'error')
            return []
            
        return list(positions)
        
    def place_order(self, request: Dict) -> Optional[Dict]:
        """주문 실행"""
        if not self.check_connection():
            return None
            
        retry_count = self.max_retries
        while retry_count > 0:
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self._log(f"주문 성공: {request['symbol']}")
                return result
                
            self._log(f"주문 실패: {result.comment}, 재시도... ({retry_count})", 'warning')
            time.sleep(self.retry_delay)
            retry_count -= 1
            
        self._log(f"주문 실패: {request['symbol']}", 'error')
        return None
        
    def modify_order(self, request: Dict) -> bool:
        """주문 수정"""
        if not self.check_connection():
            return False
            
        retry_count = self.max_retries
        while retry_count > 0:
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self._log(f"주문 수정 성공: {request['position']}")
                return True
                
            self._log(f"주문 수정 실패: {result.comment}, 재시도... ({retry_count})", 'warning')
            time.sleep(self.retry_delay)
            retry_count -= 1
            
        self._log(f"주문 수정 실패: {request['position']}", 'error')
        return False
        
    def cancel_order(self, ticket: int) -> bool:
        """주문 취소"""
        if not self.check_connection():
            return False
            
        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }
        
        retry_count = self.max_retries
        while retry_count > 0:
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self._log(f"주문 취소 성공: {ticket}")
                return True
                
            self._log(f"주문 취소 실패: {result.comment}, 재시도... ({retry_count})", 'warning')
            time.sleep(self.retry_delay)
            retry_count -= 1
            
        self._log(f"주문 취소 실패: {ticket}", 'error')
        return False