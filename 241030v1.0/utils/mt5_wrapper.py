class MT5Wrapper:
    def __init__(self):
        print("MT5Wrapper 초기화")
        
    def initialize(self):
        print("initialize: MT5 초기화")
        return True
        
    def shutdown(self):
        print("shutdown: MT5 종료")
        pass
        
    def get_positions(self, symbol):
        print(f"get_positions: {symbol} MT5 포지션 조회")
        return [] 