import MetaTrader5 as mt5
from datetime import datetime
import time

from core.time_sync import TimeSync
from core.data_feed import DataFeed
from core.position import PositionManager
from core.technical import TechnicalAnalysis
from utils.mt5_wrapper import MT5Wrapper
from utils.logger import Logger
from utils.config import Config

class Trader:
    """메인 트레이딩 시스템"""
    def __init__(self, config_path: str = "config.yaml"):
        """초기화"""
        # 1. 설정 로드
        self.config = Config(config_path)
        self.symbols = self.config.get_symbols()
        
        # 2. 로거 초기화
        self.logger = Logger(self.config.get_log_path(), "vTrader")
        self.logger.info("시스템 초기화 시작")
        
        # 3. MT5 래퍼 초기화
        self.mt5 = MT5Wrapper(self.logger)
        if not self.mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 4. 핵심 모듈 초기화
        self.time_sync = TimeSync()
        self.data_feed = DataFeed(self.symbols, self.logger)
        self.position_manager = PositionManager(
            mt5_wrapper=self.mt5,
            logger=self.logger,
            max_units=self.config.get_risk_params()['max_units'],
            max_units_per_symbol=self.config.get_risk_params()['max_units_per_symbol']
        )
        self.technical = TechnicalAnalysis()
        
        self.logger.info("시스템 초기화 완료")
        
    def run(self):
        """메인 루프"""
        try:
            while True:
                # 1. 정각 대기
                self.time_sync.wait_for_next_minute()
                
                # 2. 데이터 업데이트
                self.data_feed.update()
                
                # 3. 포지션 동기화
                self.position_manager.sync_positions()
                
                # 4. 각 심볼별 처리
                for symbol in self.symbols:
                    self._process_symbol(symbol)
                    
        except KeyboardInterrupt:
            self.logger.info("프로그램 종료 요청")
        except Exception as e:
            self.logger.error(f"예기치 않은 오류: {e}")
        finally:
            self._cleanup()
            
    def _process_symbol(self, symbol: str):
        """심볼별 처리"""
        # 1. 데이터 검증
        df = self.data_feed.get_data(symbol)
        if df is None or len(df) < self.technical.min_periods:
            return
            
        # 2. 기술적 지표 계산
        df = self.technical.calculate_indicators(df)
        
        # 3. 포지션 상태 확인
        positions = self.position_manager.get_positions(symbol)
        
        # 4. 포지션이 있는 경우
        if positions:
            self._handle_active_positions(symbol, positions, df)
        # 5. 포지션이 없는 경우
        else:
            self._handle_new_entry(symbol, df)
            
    def _handle_active_positions(self, symbol: str, positions: list, df):
        """활성 포지션 처리"""
        for position in positions:
            # 1. 청산 신호 확인
            if self.technical.check_close_signal(df, position.type):
                self._close_position(symbol, position)
                continue
                
            # 2. 손절가 업데이트
            self._update_stop_loss(symbol, position, df)
            
    def _handle_new_entry(self, symbol: str, df):
        """신규 진입 처리"""
        # 1. 진입 신호 확인
        signal = self.technical.check_entry_signal(df)
        if not signal:
            return
            
        # 2. 포지션 생성
        self._create_position(symbol, signal, df)
        
    def _create_position(self, symbol: str, signal: str, df):
        """포지션 생성"""
        # 구현 예정
        pass
        
    def _close_position(self, symbol: str, position):
        """포지션 청산"""
        # 구현 예정
        pass
        
    def _update_stop_loss(self, symbol: str, position, df):
        """손절가 업데이트"""
        # 구현 예정
        pass
        
    def _cleanup(self):
        """종료 처리"""
        self.logger.info("시스템 종료")
        self.mt5.shutdown()

def main():
    """메인 함수"""
    try:
        trader = Trader()
        trader.run()
    except Exception as e:
        print(f"치명적 오류: {e}")

if __name__ == "__main__":
    main()