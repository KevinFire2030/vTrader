import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import time

class LiveFeed:
    def __init__(self, symbols):
        self.symbols = symbols
        self.data_dict = {}
        
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        self._initialize_data()
    
    def _initialize_data(self):
        """초기 데이터 로드"""
        for symbol in self.symbols:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 61)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                self.data_dict[symbol] = df[:-1]  # 60개의 완성된 봉
    
    def update(self):
        """데이터 업데이트"""
        server_time = mt5.symbol_info_tick(self.symbols[0]).time
        current_minute = datetime.utcfromtimestamp(server_time).replace(second=0, microsecond=0)
        
        for symbol in self.symbols:
            # 현재 시간 기준으로 최근 봉 3개 요청
            rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, server_time, 3)
            if rates is not None and len(rates) >= 2:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                
                # 현재 분 이전의 봉들만 선택
                completed_candles = df[df.index < current_minute]
                if not completed_candles.empty:
                    # 기존 데이터 업데이트
                    self.data_dict[symbol] = pd.concat([
                        self.data_dict[symbol],
                        completed_candles.iloc[[-1]]  # 마지막 완성된 봉
                    ]).tail(60)
    
    def get_data(self, symbol):
        """심볼의 데이터 반환"""
        return self.data_dict.get(symbol)

def main():
    """테스트 실행"""
    # Market Watch에서 심볼 가져오기
    symbols = []
    if mt5.initialize():
        for symbol in mt5.symbols_get():
            if symbol.visible and len(symbols) < 10:
                symbols.append(symbol.name)
        mt5.shutdown()
    
    if not symbols:
        print("심볼을 찾을 수 없습니다.")
        return
    
    # LiveFeed 인스턴스 생성
    feed = LiveFeed(symbols)
    
    try:
        while True:
            feed.wait_for_next_minute()  # 다음 분의 정각까지 대기
            feed.update()  # 데이터 업데이트
            
    except KeyboardInterrupt:
        print("\n프로그램 종료")

if __name__ == '__main__':
    main()
