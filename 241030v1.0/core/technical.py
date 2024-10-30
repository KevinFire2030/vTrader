class TechnicalAnalysis:
    def __init__(self):
        print("TechnicalAnalysis 초기화")
        self.atr_period = 20
        self.ema_short = 5
        self.ema_mid = 20
        self.ema_long = 40
        self.min_periods = 40
        
    def calculate_indicators(self, df):
        print("calculate_indicators: 지표 계산")
        return df
        
    def generate_signal(self, df):
        print("generate_signal: 거래 신호 생성")
        return None
        
    def check_close_signal(self, df, symbol, position_type):
        print(f"check_close_signal: {symbol} 청산 신호 확인")
        return False 