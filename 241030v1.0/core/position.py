from datetime import datetime, timedelta
from typing import Optional, Dict, List

class Position:
    """단일 포지션 정보"""
    def __init__(self):
        # 기본 정보
        self.ticket = None        # MT5 티켓 번호
        self.symbol = None        # 거래 심볼
        self.type = None         # 'BUY' or 'SELL'
        self.volume = None       # 거래량
        
        # 가격 정보
        self.entry_price = None  # 진입가
        self.exit_price = None   # 청산가
        self.sl_price = None     # 손절가
        self.tp_price = None     # 이익실현가
        
        # 시간 정보
        self.entry_time = None   # 진입시간
        self.exit_time = None    # 청산시간
        self.lifetime = None     # 포지션 유지 기간
        
        # 손익 정보
        self.commission = None   # 수수료
        self.swap = None         # 스왑 포인트
        self.profit = None       # 실현 손익
        self.upnl = None         # 미실현 손익
        self.max_profit = None   # 최대 이익
        self.max_loss = None     # 최대 손실
        self.risk_amount = None  # 리스크 금액
        
        # 기술적 정보
        self.entry_atr = None    # 진입시 ATR
        self.comment = None      # 포지션 코멘트
        
        # 상태 정보
        self.status = 'PENDING'  # PENDING/OPEN/CLOSED

    def close(self, exit_price: float, exit_time: datetime):
        """포지션 청산"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.lifetime = exit_time - self.entry_time
        
        # 손익 계산
        if self.type == 'BUY':
            self.profit = (exit_price - self.entry_price) * self.volume
        else:
            self.profit = (self.entry_price - exit_price) * self.volume
            
        # 수수료와 스왑 반영
        if self.commission:
            self.profit -= self.commission
        if self.swap:
            self.profit += self.swap
            
        # 상태 업데이트
        self.status = 'CLOSED'
        self.upnl = None  # 청산 후에는 미실현 손익 없음
        
        # 최대 손익 업데이트
        if self.profit > (self.max_profit or 0):
            self.max_profit = self.profit
        if self.profit < (self.max_loss or 0):
            self.max_loss = self.profit

    def update_state(self, current_price: float):
        """포지션 태 업데이트"""
        # 미실현 손익 계산
        self.update_upnl(current_price)
        
        # 보유 시간 업데이트
        if self.is_open():
            self.lifetime = datetime.utcnow() - self.entry_time
            
        # 최대 손익 업데이트
        if self.upnl > (self.max_profit or 0):
            self.max_profit = self.upnl
        if self.upnl < (self.max_loss or 0):
            self.max_loss = self.upnl

    def update_upnl(self, current_price: float):
        """미실현 손익 업데이트"""
        if self.type == 'BUY':
            self.upnl = (current_price - self.entry_price) * self.volume
        else:
            self.upnl = (self.entry_price - current_price) * self.volume
            
        # 수수료와 스왑 반영
        if self.commission:
            self.upnl -= self.commission
        if self.swap:
            self.upnl += self.swap

    def get_risk_amount(self) -> float:
        """리스크 금액 계산"""
        if self.entry_price is None or self.sl_price is None:
            return 0.0
        risk_per_unit = abs(self.entry_price - self.sl_price)
        return risk_per_unit * self.volume

    def get_max_loss(self) -> float:
        """최대 손실 계산"""
        return self.get_risk_amount()

    def get_max_profit(self) -> float:
        """최대 이익 계산"""
        if self.is_closed():
            return self.profit
        return max(self.profit or 0, self.upnl or 0)

    def is_long(self) -> bool:
        """롱 포지션 여부"""
        return self.type == 'BUY'

    def is_short(self) -> bool:
        """숏 포지션 여부"""
        return self.type == 'SELL'

    def is_open(self) -> bool:
        """포지션 오픈 여부"""
        return self.exit_time is None

    def is_closed(self) -> bool:
        """포지션 청산 여부"""
        return self.exit_time is not None

    def get_holding_time(self) -> timedelta:
        """포지션 보유 시간"""
        if self.is_open():
            return datetime.utcnow() - self.entry_time
        return self.lifetime

    def get_profit(self) -> float:
        """포지션 손익"""
        if self.is_closed():
            return self.profit
        return self.upnl

    def validate(self) -> bool:
        """데이터 무결성 검증"""
        if None in [self.ticket, self.symbol, self.type, self.volume, 
                   self.entry_price, self.entry_time]:
            return False
        
        if self.type not in ['BUY', 'SELL']:
            return False
            
        if self.volume <= 0:
            return False
            
        if self.entry_price <= 0:
            return False
            
        if self.sl_price and self.sl_price <= 0:
            return False
            
        return True

class PositionManager:
    """포지션 관리"""
    def __init__(self, mt5_wrapper=None, logger=None):
        self.mt5 = mt5_wrapper
        self.logger = logger
        self.active_positions: Dict[str, List[Position]] = {}
        self.closed_positions: List[Position] = []
        self.total_units = 0
        self.max_units = 15
        self.max_units_per_symbol = 4

    def _log(self, message: str, level: str = 'info'):
        """로그 출력"""
        if self.logger:
            getattr(self.logger, level)(message)
            
    def can_add_position(self, symbol: str) -> bool:
        """포지션 추가 가능 여부 확인"""
        # MT5의 실제 포지션 수 확인
        if self.mt5:
            mt5_positions = self.mt5.get_positions(symbol)
            current_positions = len(mt5_positions) if mt5_positions else 0
            
            if current_positions >= self.max_units_per_symbol:
                self._log(f"{symbol} 최대 유닛 수 초과: {current_positions}/{self.max_units_per_symbol}")
                return False
        
        # Position Manager의 포지션 수 확인
        symbol_positions = self.active_positions.get(symbol, [])
        if len(symbol_positions) >= self.max_units_per_symbol:
            self._log(f"{symbol} 최대 유닛 수 초과: {len(symbol_positions)}/{self.max_units_per_symbol}")
            return False
        
        if self.total_units >= self.max_units:
            self._log(f"전체 최대 유닛 수 초과: {self.total_units}/{self.max_units}")
            return False
        
        return True

    def add_position(self, position: Position) -> bool:
        """포지션 추가"""
        if not self.can_add_position(position.symbol):
            return False
            
        if position.symbol not in self.active_positions:
            self.active_positions[position.symbol] = []
            
        self.active_positions[position.symbol].append(position)
        self.total_units += 1
        
        self._log(f"{position.symbol} {position.type} 포지션 추가 (티켓: {position.ticket})")
        return True

    def close_position(self, symbol: str, ticket: int, exit_price: float, exit_time: datetime) -> bool:
        """포지션 청산"""
        if symbol not in self.active_positions:
            self._log(f"{symbol} 활성 포지션 없음", 'warning')
            return False
            
        # 실제 MT5 포지션 확인
        if self.mt5:
            mt5_positions = self.mt5.get_positions(symbol)
            mt5_tickets = set() if mt5_positions is None else {pos.ticket for pos in mt5_positions}
            if ticket not in mt5_tickets:
                self._log(f"{symbol} 티켓 {ticket}이 이미 청산됨", 'info')
        
        # Position Manager 업데이트
        for i, pos in enumerate(self.active_positions[symbol]):
            if pos.ticket == ticket:
                pos.close(exit_price, exit_time)
                self.closed_positions.append(pos)
                self.active_positions[symbol].pop(i)
                self.total_units -= 1
                
                if not self.active_positions[symbol]:
                    del self.active_positions[symbol]
                    
                self._log(f"{symbol} 포지션 청산 (티켓: {ticket}, 수익: {pos.profit})")
                return True
                
        self._log(f"{symbol} 티켓 {ticket} 찾을 수 없음", 'warning')
        return False

    def get_positions(self, symbol: str) -> List[Position]:
        """심볼의 활성 포지션 조회"""
        return self.active_positions.get(symbol, [])

    def update_sl(self, symbol: str, ticket: int, new_sl: float) -> bool:
        """손절가 수정"""
        if symbol not in self.active_positions:
            self._log(f"{symbol} 활성 포지션 없음", 'warning')
            return False
            
        for pos in self.active_positions[symbol]:
            if pos.ticket == ticket:
                pos.sl_price = new_sl
                self._log(f"{symbol} 손절가 수정 (티켓: {ticket}, 새 손절가: {new_sl})")
                return True
                
        self._log(f"{symbol} 티켓 {ticket} 찾을 수 없음", 'warning')
        return False

    def get_total_profit(self) -> float:
        """전체 포지션 손익"""
        total = 0.0
        for positions in self.active_positions.values():
            for pos in positions:
                total += pos.get_profit()
        return total

    def sync_positions(self):
        """MT5 실제 포지션과 동기화"""
        if not self.mt5:
            return
            
        for symbol in list(self.active_positions.keys()):
            # MT5의 실제 포지션 확인
            mt5_positions = self.mt5.get_positions(symbol)
            mt5_tickets = set() if mt5_positions is None else {pos.ticket for pos in mt5_positions}
            
            # Position Manager의 포지션 확인
            for pos in self.active_positions[symbol][:]:  # 복사본으로 순회
                if pos.ticket not in mt5_tickets:
                    self._log(f"{symbol} 포지션 자동 청산 감지 (티켓: {pos.ticket})")
                    self.close_position(symbol, pos.ticket, pos.entry_price, datetime.utcnow())