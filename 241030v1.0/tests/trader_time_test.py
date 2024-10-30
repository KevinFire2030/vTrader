import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import MetaTrader5 as mt5
import time
from datetime import datetime
from core.time_sync import TimeSync
from core.data_feed import DataFeed
from utils.logger import Logger

class TraderTimeTest:
    """정각 데이터 수신 테스트"""
    def __init__(self):
        # MT5 초기화
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 테스트 설정
        self.symbol = "#USNDAQ100"
        
        # 모듈 초기화
        self.logger = Logger("logs", "trader_time_test")
        self.time_sync = TimeSync()
        self.data_feed = DataFeed([self.symbol], self.logger)
        
        self.logger.info("초기화 완료")
        
    def test_minute_data(self):
        """정각 데이터 수신 테스트"""
        self.logger.info("\n=== 정각 데이터 수신 테스트 ===")
        
        try:
            while True:
                # 1. 정각 대기
                self.time_sync.wait_for_next_minute()
                server_time = self.time_sync.get_server_time()
                current_time = datetime.utcfromtimestamp(server_time)
                self.logger.info(f"정각 도달: {current_time}")
                
                # 2. 데이터 업데이트
                self.data_feed.update()
                
                # 3. 데이터 검증
                df = self.data_feed.get_data(self.symbol)
                if df is not None:
                    last_candle = df.iloc[-1]
                    self.logger.info(f"\n마지막 봉 정보:")
                    self.logger.info(f"시간: {df.index[-1]}")
                    self.logger.info(f"시가: {last_candle['open']:.5f}")
                    self.logger.info(f"고가: {last_candle['high']:.5f}")
                    self.logger.info(f"저가: {last_candle['low']:.5f}")
                    self.logger.info(f"종가: {last_candle['close']:.5f}")
                    self.logger.info(f"볼륨: {last_candle['tick_volume']}")
                    
                # 4. 데이터 무결성 검증
                if not self.data_feed.validate_data(self.symbol):
                    self.logger.error("데이터 무결성 검증 실패")
                    
                time.sleep(1)  # CPU 부하 방지
                
        except KeyboardInterrupt:
            self.logger.info("테스트 종료")
        finally:
            mt5.shutdown()

def main():
    """메인 함수"""
    try:
        tester = TraderTimeTest()
        tester.test_minute_data()
    except Exception as e:
        print(f"테스트 실패: {e}")

if __name__ == '__main__':
    main() 