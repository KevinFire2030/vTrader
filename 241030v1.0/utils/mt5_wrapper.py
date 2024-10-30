import MetaTrader5 as mt5
from datetime import datetime
import time
from typing import Dict, List, Optional, Any, Union
from threading import Lock

class MT5Wrapper:
    """MT5 API 래퍼"""
    def __init__(self, logger=None):
        self.logger = logger
        self.max_retries = 3
        self.retry_delay = 1.0
        self.initialized = False
        self._lock = Lock()
        
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
            
        # 실제 MT5 포지션 조회
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            self._log(f"{symbol} 포지션 조회 실패", 'error')
            return []
            
        # 포지션 정보를 리스트로 변환
        position_list = []
        for pos in positions:
            position_info = {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                'volume': pos.volume,
                'price': pos.price_open,
                'sl': pos.sl,
                'tp': pos.tp,
                'time': datetime.utcfromtimestamp(pos.time),
                'magic': pos.magic,
                'profit': pos.profit,
                'comment': pos.comment
            }
            position_list.append(position_info)
            
        return position_list
        
    def place_order(self, request: Dict) -> Optional[Dict]:
        """주문 실행"""
        if not self.check_connection():
            return None
            
        with self._lock:
            # 1. 주문 실행 전에 포지션 수 확인
            symbol = request.get('symbol')
            mt5_positions = mt5.positions_get(symbol=symbol)
            current_positions = len(mt5_positions) if mt5_positions else 0
            
            if current_positions >= 4:  # 심볼당 최대 4개
                self._log(f"{symbol} 최대 포지션 수 초과: {current_positions}/4", 'warning')
                return None
                
            # 2. 주문 실행
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self._log(f"주문 실패: {result.comment}", 'error')
                return None
                
            # 3. 주문 실행 후 즉시 포지션 수 재확인
            mt5_positions = mt5.positions_get(symbol=symbol)
            current_positions = len(mt5_positions) if mt5_positions else 0
            
            if current_positions > 4:  # 최대 수를 초과했다면
                # 마지막 주문 즉시 청산
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": request["volume"],
                    "type": mt5.ORDER_TYPE_SELL if request["type"] == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                    "position": result.order,
                    "magic": request.get("magic", 0),
                    "comment": "position limit exceeded",
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                mt5.order_send(close_request)
                self._log(f"{symbol} 포지션 수 제한으로 인한 자동 청산", 'warning')
                return None
                
            return result
        
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