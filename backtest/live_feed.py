import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import time

class LiveFeed:
    def __init__(self, symbols):
        """실시간 데이터 피드 초기화"""
        self.symbols = symbols
        self.data_dict = {}  # 각 심볼의 데이터를 저장할 딕셔너리
        
        # MT5 초기화
        if not mt5.initialize():
            print("MT5 초기화 실패")
            return
            
        # 초기 데이터 로드 (60개 1분봉)
        self._initialize_data()
        
    def _initialize_data(self):
        """각 심볼의 초기 데이터 로드"""
        current_time = mt5.symbol_info_tick(self.symbols[0]).time
        from_time = current_time - (60 * 60)  # 60분을 초 단위로 계산

        for symbol in self.symbols:
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, current_time)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                
                print(f"\n{symbol} 초기 데이터:")
                print(f"데이터 개수: {len(df)}")
                print(f"시작: {df.index[0]}")
                print(f"종료: {df.index[-1]}")
                
                self.data_dict[symbol] = df
            else:
                print(f"\n{symbol} 데이터 없음")
    
    def wait_for_next_minute(self):
        """다음 분의 정각(00초)까지 대기"""
        current_time = mt5.symbol_info_tick(self.symbols[0]).time
        seconds = current_time % 60  # 현재 초
        wait_seconds = 60 - seconds  # 다음 분까지 남은 초
        
        if wait_seconds > 0:
            print(f"다음 업데이트까지 {wait_seconds}초 대기")
            time.sleep(wait_seconds)
    
    def update(self):
        """실시간 데이터 업데이트"""
        for symbol in self.symbols:
            last_time = self.data_dict[symbol].index[-1]
            current_time = mt5.symbol_info_tick(symbol).time
            
            if current_time - last_time.timestamp() >= 60:
                new_rates = mt5.copy_rates_range(
                    symbol, 
                    mt5.TIMEFRAME_M1,
                    int(last_time.timestamp()),
                    current_time
                )
                
                if new_rates is not None and len(new_rates) > 0:
                    new_df = pd.DataFrame(new_rates)
                    new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
                    new_df.set_index('time', inplace=True)
                    
                    self.data_dict[symbol] = pd.concat([
                        self.data_dict[symbol][:-1],
                        new_df
                    ]).tail(60)
                    
                    # 마지막 두 개 봉의 정보 출력
                    last_bars = self.data_dict[symbol].tail(2)
                    print(f"\n{symbol} 데이터 업데이트:")
                    for i, (index, bar) in enumerate(last_bars.iterrows()):
                        bar_type = "미완성 봉 [-1]" if i == 1 else "완성된 마지막 봉 [-2]"
                        print(f"\n{bar_type}: {index}")
                        print(f"시가: {bar['open']:.2f}")
                        print(f"고가: {bar['high']:.2f}")
                        print(f"저가: {bar['low']:.2f}")
                        print(f"종가: {bar['close']:.2f}")
                        print(f"거래량: {bar['real_volume']}")
                        if i == 1:
                            print("※ 주의: 미완성 봉은 매매 판단에 사용하지 않음")
                    
                    print(f"\n현재 데이터 개수: {len(self.data_dict[symbol])}")
    
    def get_data(self, symbol):
        """특정 심볼의 현재 데이터 반환"""
        return self.data_dict.get(symbol)
    
    def __del__(self):
        """소멸자"""
        mt5.shutdown()

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
