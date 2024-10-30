import MetaTrader5 as mt5
from datetime import datetime
import time

# 핵심 모듈 임포트
from core.time_sync import TimeSync
from core.data_feed import DataFeed
from core.position import PositionManager
from core.pyramid import PyramidManager
from core.technical import TechnicalAnalysis

# 유틸리티 임포트
from utils.mt5_wrapper import MT5Wrapper
from utils.logger import Logger
from utils.config import Config

class Trader:
    """메인 트레이딩 시스템"""
    def __init__(self, config_path="config.yaml"):
        """
        초기화 흐름:
        1. 설정 파일 로드
        2. MT5 연결
        3. 심볼 목록 확인
        4. 각 모듈 초기화
        5. 기존 포지션 확인
        """
        # 설정 로드
        self.config = Config(config_path)
        
        # MT5 래퍼 초기화
        self.mt5 = MT5Wrapper()
        if not self.mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 심볼 목록 설정
        self.symbols = self.config.get_symbols()
        if not self.symbols:
            raise Exception("거래 가능한 심볼 없음")
            
        # 로거 초기화
        self.logger = Logger(self.config.get_log_path())
        
        # 핵심 모듈 초기화
        self.time_sync = TimeSync()
        self.data_feed = DataFeed(self.symbols)
        self.position_manager = PositionManager()
        self.pyramid_manager = PyramidManager()
        self.technical = TechnicalAnalysis()
        
        # 기존 포지션 확인
        self._check_existing_positions()
        
        self.logger.info("시스템 초기화 완료")

    def _check_existing_positions(self):
        """기존 포지션 확인 및 복구"""
        for symbol in self.symbols:
            positions = self.mt5.get_positions(symbol)
            if positions:
                self.logger.info(f"{symbol} 기존 포지션 발견: {len(positions)}개")
                # 포지션 정보 복구
                
    def run(self):
        """
        메인 루프 흐름:
        1. 매분 정각(00초) 대기
        2. 데이터 업데이트
        3. 포지션 동기화
        4. 각 심볼별 처리
           - 기술적 지표 계산
           - 포지션 상태 확인
           - 거래 신호 처리
        """
        try:
            while True:
                # 1. 정각 대기
                self.time_sync.wait_for_next_minute()
                
                # 2. 데이터 업데이트
                self.data_feed.update()
                
                # 3. 포지션 동기화
                self._sync_positions()
                
                # 4. 각 심볼별 처리
                for symbol in self.symbols:
                    self._process_symbol(symbol)
                    
        except KeyboardInterrupt:
            self.logger.info("프로그램 종료 요청")
        except Exception as e:
            self.logger.error(f"예기치 않은 오류: {e}")
        finally:
            self._cleanup()

    def _sync_positions(self):
        """
        포지션 동기화:
        1. MT5 실제 포지션 확인
        2. 자동 청산 감지
        3. 포지션 정보 업데이트
        """
        for symbol in self.symbols:
            pass  # 구현 예정

    def _process_symbol(self, symbol):
        """
        심볼별 처리:
        1. 데이터 검증
        2. 기술적 지표 계산
        3. 포지션 상태 확인
        4. 거래 신호 처리
        """
        # 1. 데이터 검증
        df = self.data_feed.get_data(symbol)
        if df is None or len(df) < self.technical.min_periods:
            return
            
        # 2. 기술적 지표 계산
        df = self.technical.calculate_indicators(df)
        
        # 3. 포지션 상태 확인
        positions = self.position_manager.get_positions(symbol)
        
        # 4. 거래 신호 처리
        if positions:
            self._handle_active_position(symbol, positions, df)
        else:
            self._handle_new_signal(symbol, df)

    def _handle_active_position(self, symbol, positions, df):
        """
        활성 포지션 처리:
        1. 청산 신호 확인
        2. 피라미딩 신호 확인
        3. 손절가 관리
        """
        pass  # 구현 예정

    def _handle_new_signal(self, symbol, df):
        """
        신규 진입 처리:
        1. 진입 신호 확인
        2. 포지션 크기 계산
        3. 주문 실행
        4. 피라미딩 주문 설정
        """
        pass  # 구현 예정

    def _cleanup(self):
        """
        종료 처리:
        1. 포지션 정보 저장
        2. 로그 정리
        3. MT5 연결 종료
        """
        self.logger.info("종료 처리 시작")
        self.mt5.shutdown()

def main():
    """
    메인 함수:
    1. 설정 파일 경로 확인
    2. Trader 인스턴스 생성
    3. 트레이딩 시작
    """
    try:
        trader = Trader("config.yaml")
        trader.run()
    except Exception as e:
        print(f"치명적 오류: {e}")

if __name__ == "__main__":
    main()