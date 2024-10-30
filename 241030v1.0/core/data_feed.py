import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

class DataFeed:
    """실시간 데이터 관리"""
    def __init__(self, symbols, logger=None):
        self.symbols = symbols
        self.data_dict = {}  # symbol: DataFrame
        self.candle_count = 60  # 유지할 봉 개수
        self.logger = logger
        
        # 초기 데이터 로드
        self._initialize_data()
        
    def _log(self, message):
        """로그 출력"""
        if self.logger:
            self.logger.info(message)
        print(message)
        
    def _initialize_data(self):
        """초기 60개의 봉 데이터 로드"""
        for symbol in self.symbols:
            # 안전하게 65개 요청 (마지막 미완성 봉 + 여유분)
            rates = mt5.copy_rates_from_pos(
                symbol,
                mt5.TIMEFRAME_M1,
                0,
                self.candle_count + 5
            )
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                
                # 현재 시간 확인
                server_time = mt5.symbol_info_tick(symbol).time
                current_minute = datetime.utcfromtimestamp(server_time).replace(second=0, microsecond=0)
                
                # 현재 분보다 이전의 봉만 선택 (완성된 봉)
                completed_data = df[df.index < current_minute].tail(self.candle_count)
                self.data_dict[symbol] = completed_data
                
                self._log(f"\n{symbol} 초기 데이터:")
                self._log(f"완성된 봉 개수: {len(completed_data)}")
                self._log(f"시작: {completed_data.index[0]}")
                self._log(f"종료: {completed_data.index[-1]}")
                
                # 데이터 검증
                if not self.validate_data(symbol):
                    raise Exception(f"{symbol} 초기 데이터 검증 실패")
    
    def update(self):
        """실시간 데이터 업데이트"""
        for symbol in self.symbols:
            # 서버 시간 확인
            server_time = mt5.symbol_info_tick(symbol).time
            current_minute = datetime.utcfromtimestamp(server_time).replace(second=0, microsecond=0)
            
            # 최근 5개 봉 요청 (안전하게)
            rates = mt5.copy_rates_from(
                symbol,
                mt5.TIMEFRAME_M1,
                server_time,
                5
            )
            
            if rates is not None and len(rates) >= 2:
                new_df = pd.DataFrame(rates)
                new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
                new_df.set_index('time', inplace=True)
                
                # 현재 분보다 이전의 봉만 선택 (완성된 봉)
                completed_candles = new_df[new_df.index < current_minute]
                if not completed_candles.empty:
                    # 마지막 완성된 봉
                    last_candle = completed_candles.iloc[-1]
                    
                    # 기존 데이터가 있는 경우
                    if symbol in self.data_dict and not self.data_dict[symbol].empty:
                        # 마지막 봉 시간 비교
                        if last_candle.name > self.data_dict[symbol].index[-1]:
                            # 새로운 봉 추가
                            self.data_dict[symbol] = pd.concat([
                                self.data_dict[symbol],
                                completed_candles.iloc[[-1]]
                            ]).tail(self.candle_count)
                            
                            self._log(f"\n새로운 봉 추가: {last_candle.name}")
                            self._log(f"시가: {last_candle['open']:.5f}")
                            self._log(f"고가: {last_candle['high']:.5f}")
                            self._log(f"저가: {last_candle['low']:.5f}")
                            self._log(f"종가: {last_candle['close']:.5f}")
                            self._log(f"볼륨: {last_candle['tick_volume']}")
                            
                            # 데이터 검증
                            if not self.validate_data(symbol):
                                self._log(f"경고: {symbol} 데이터 검증 실패")
                    else:
                        # 기존 데이터가 없는 경우 새로 생성
                        self.data_dict[symbol] = completed_candles.tail(self.candle_count)
    
    def get_data(self, symbol):
        """심볼의 데이터 반환"""
        return self.data_dict.get(symbol)
    
    def validate_data(self, symbol):
        """데이터 무결성 검증"""
        df = self.data_dict.get(symbol)
        if df is None or len(df) == 0:
            self._log(f"경고: {symbol} 데이터 없음")
            return False
            
        # 1. 봉 개수 확인
        if len(df) > self.candle_count:
            self._log(f"경고: {symbol}의 봉 개수가 {len(df)}개입니다.")
            return False
            
        # 2. 시간 순서 확인
        if not df.index.is_monotonic_increasing:
            self._log(f"경고: {symbol}의 시간 순서가 올바르지 않습니다.")
            return False
            
        # 3. 시간 간격 확인
        time_diff = df.index.to_series().diff()
        if not all(time_diff[1:] == timedelta(minutes=1)):
            self._log(f"경고: {symbol}의 시간 간격이 1분이 아닌 구간이 있습니다.")
            return False
            
        # 4. 가격 데이터 확인
        if df['high'].min() < 0 or df['low'].min() < 0:
            self._log(f"경고: {symbol}의 가격이 음수입니다.")
            return False
            
        if not all(df['high'] >= df['low']):
            self._log(f"경고: {symbol}의 고가가 저가보다 낮은 구간이 있습니다.")
            return False
            
        return True