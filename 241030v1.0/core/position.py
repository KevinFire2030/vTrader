class Position:
    """단일 포지션 정보"""
    def __init__(self):
        self.ticket = None
        self.type = None
        self.volume = None
        self.entry_price = None
        self.sl_price = None
        self.entry_time = None
        self.entry_atr = None

class PositionManager:
    """포지션 관리"""
    def __init__(self):
        print("PositionManager 초기화")
        self.active_positions = {}
        self.closed_positions = []
        self.total_units = 0
        self.max_units = 15
        self.max_units_per_symbol = 4
        
    def can_add_position(self, symbol):
        print(f"can_add_position: {symbol} 포지션 추가 가능 여부 확인")
        return True
        
    def add_position(self, symbol, position):
        print(f"add_position: {symbol} 포지션 추가")
        return True
        
    def get_positions(self, symbol):
        print(f"get_positions: {symbol} 포지션 조회")
        return []
        
    def update_sl(self, symbol, ticket, new_sl):
        print(f"update_sl: {symbol} 손절가 업데이트")
        return True