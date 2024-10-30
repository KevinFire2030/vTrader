import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import MetaTrader5 as mt5
import time
from datetime import datetime
from core.time_sync import TimeSync
from core.data_feed import DataFeed
from core.position import PositionManager
from core.technical import TechnicalAnalysis
from utils.mt5_wrapper import MT5Wrapper
from utils.logger import Logger

class TraderIntegrationTest:
    """트레이더 통합 테스트"""
    def __init__(self):
        # MT5 초기화
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 테스트 설정
        self.symbol = "#USNDAQ100"
        self.volume = 0.01
        self.magic = 241030
        
        # 모듈 초기화
        self.logger = Logger("logs", "integration_test")
        self.logger.info("통합 테스트 시작")
        
        # MT5Wrapper 초기화
        self.mt5 = MT5Wrapper(self.logger)
        if not self.mt5.initialize():
            raise Exception("MT5Wrapper 초기화 실패")
            
        # 핵심 모듈 초기화
        self.time_sync = TimeSync()
        self.data_feed = DataFeed([self.symbol], self.logger)
        self.position_manager = PositionManager(
            mt5_wrapper=self.mt5,
            logger=self.logger,
            max_units_per_symbol=4
        )
        self.technical = TechnicalAnalysis()
        
        self.logger.info("초기화 완료")
        
    def test_realtime_trading(self):
        """실시간 거래 테스트"""
        self.logger.info("\n=== 실시간 거래 테스트 ===")
        
        try:
            while True:
                # 1. 정각 대기
                self.time_sync.wait_for_next_minute()
                server_time = self.time_sync.get_server_time()
                current_time = datetime.utcfromtimestamp(server_time)
                self.logger.info(f"정각 도달: {current_time}")
                
                # 2. 데이터 업데이트
                self.data_feed.update()
                
                # 3. 포지션 동기화
                self.position_manager.sync_positions()
                
                # 4. 데이터 검증
                df = self.data_feed.get_data(self.symbol)
                if df is None or len(df) < self.technical.min_periods:
                    continue
                    
                # 5. 기술적 지표 계산
                df = self.technical.calculate_indicators(df)
                last_candle = df.iloc[-1]
                
                # 6. 지표 값 출력
                self.logger.info(f"\n마지막 봉 정보:")
                self.logger.info(f"시간: {df.index[-1]}")
                self.logger.info(f"시가: {last_candle['open']:.2f}")
                self.logger.info(f"고가: {last_candle['high']:.2f}")
                self.logger.info(f"저가: {last_candle['low']:.2f}")
                self.logger.info(f"종가: {last_candle['close']:.2f}")
                self.logger.info(f"볼륨: {last_candle['tick_volume']}")
                
                self.logger.info(f"\n기술적 지표:")
                self.logger.info(f"EMA(5): {last_candle['ema_short']:.2f}")
                self.logger.info(f"EMA(20): {last_candle['ema_mid']:.2f}")
                self.logger.info(f"EMA(40): {last_candle['ema_long']:.2f}")
                self.logger.info(f"ATR(20): {last_candle['atr']:.2f}")
                
                # 7. 포지션 상태 확인
                positions = self.position_manager.get_positions(self.symbol)
                self.logger.info(f"\n포지션 상태:")
                self.logger.info(f"활성 포지션 수: {len(positions)}")
                
                # 8. 거래 신호 확인
                signal = self.technical.check_entry_signal(df)
                if signal:
                    self.logger.info(f"진입 신호 발생: {signal}")
                    
                # 9. 청산 신호 확인
                for position in positions:
                    if self.technical.check_close_signal(df, position.type):
                        self.logger.info(f"청산 신호 발생: {position.ticket}")
                        
                time.sleep(1)  # CPU 부하 방지
                
        except KeyboardInterrupt:
            self.logger.info("테스트 종료")
        finally:
            mt5.shutdown()

def main():
    """메인 함수"""
    try:
        tester = TraderIntegrationTest()
        tester.test_realtime_trading()
    except Exception as e:
        print(f"테스트 실패: {e}")
        if mt5.initialize():
            mt5.shutdown()

if __name__ == '__main__':
    main() 