import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import MetaTrader5 as mt5
import time
from datetime import datetime
from core.time_sync import TimeSync
from core.data_feed import DataFeed
from core.technical import TechnicalAnalysis
from utils.logger import Logger

class TraderTechnicalTest:
    """실시간 지표 계산 테스트"""
    def __init__(self):
        # MT5 초기화
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 테스트 설정
        self.symbol = "#USNDAQ100"
        
        # 모듈 초기화
        self.logger = Logger("logs", "trader_technical_test")
        self.time_sync = TimeSync()
        self.data_feed = DataFeed([self.symbol], self.logger)
        self.technical = TechnicalAnalysis()
        
        self.logger.info("초기화 완료")
        
    def test_realtime_indicators(self):
        """실시간 지표 계산 테스트"""
        self.logger.info("\n=== 실시간 지표 계산 테스트 ===")
        
        try:
            while True:
                # 1. 정각 대기
                self.time_sync.wait_for_next_minute()
                server_time = self.time_sync.get_server_time()
                current_time = datetime.utcfromtimestamp(server_time)
                self.logger.info(f"정각 도달: {current_time}")
                
                # 2. 데이터 업데이트
                self.data_feed.update()
                
                # 3. 지표 계산
                df = self.data_feed.get_data(self.symbol)
                if df is not None:
                    df = self.technical.calculate_indicators(df)
                    last_candle = df.iloc[-1]
                    
                    # 4. 지표 값 출력
                    self.logger.info(f"\n마지막 봉 지표:")
                    self.logger.info(f"시간: {df.index[-1]}")
                    self.logger.info(f"EMA(5): {last_candle['ema_short']:.2f}")
                    self.logger.info(f"EMA(20): {last_candle['ema_mid']:.2f}")
                    self.logger.info(f"EMA(40): {last_candle['ema_long']:.2f}")
                    self.logger.info(f"ATR(20): {last_candle['atr']:.2f}")
                    
                    # 5. 거래 신호 확인
                    signal = self.technical.check_entry_signal(df)
                    if signal:
                        self.logger.info(f"진입 신호 발생: {signal}")
                    
                time.sleep(1)  # CPU 부하 방지
                
        except KeyboardInterrupt:
            self.logger.info("테스트 종료")
        finally:
            mt5.shutdown()

def main():
    """메인 함수"""
    try:
        tester = TraderTechnicalTest()
        tester.test_realtime_indicators()
    except Exception as e:
        print(f"테스트 실패: {e}")

if __name__ == '__main__':
    main() 