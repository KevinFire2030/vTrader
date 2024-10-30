import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import MetaTrader5 as mt5
import time
from datetime import datetime
from core.position import Position, PositionManager
from utils.mt5_wrapper import MT5Wrapper
from utils.logger import Logger

class PositionPyramidTest:
    """Position 모듈 피라미딩 테스트"""
    def __init__(self):
        # MT5 초기화
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 테스트 설정
        self.symbol = "#USNDAQ100"
        self.volume = 0.01
        self.magic = 241030
        
        # 모듈 초기화
        self.logger = Logger("logs", "pyramid_test")
        self.logger.info("Position 피라미딩 테스트 시작")
        
        # MT5Wrapper 초기화
        self.mt5 = MT5Wrapper(self.logger)
        if not self.mt5.initialize():
            raise Exception("MT5Wrapper 초기화 실패")
        
        # PositionManager 초기화
        self.position_manager = PositionManager(
            mt5_wrapper=self.mt5,
            logger=self.logger,
            max_units_per_symbol=4
        )
        
        # 심볼 정보 확인
        if not mt5.symbol_info(self.symbol):
            raise Exception(f"심볼 정보 없음: {self.symbol}")
        
        self.logger.info("초기화 완료")
        
    def cleanup(self):
        """종료 처리"""
        # 모든 포지션 청산
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            self.logger.info(f"남은 포지션 청산: {len(positions)}개")
            for pos in positions:
                self._close_position(pos)
                time.sleep(0.1)  # 청산 간격
                
        self.logger.info("테스트 종료")
        mt5.shutdown()
        
    def _close_position(self, mt5_pos):
        """포지션 청산"""
        symbol_info = mt5.symbol_info(self.symbol)
        if mt5_pos.type == mt5.POSITION_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            price = symbol_info.bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = symbol_info.ask
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": mt5_pos.volume,
            "type": close_type,
            "position": mt5_pos.ticket,
            "price": price,
            "magic": self.magic,
            "comment": "pyramid test close",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"청산 실패: {result.comment}")
            return False
            
        self.logger.info(f"포지션 청산 성공 (티켓: {mt5_pos.ticket})")
        return True
        
    def test_pyramid_entry(self):
        """피라미딩 진입 테스트"""
        self.logger.info("\n=== 피라미딩 진입 테스트 ===")
        
        # 1-5번째 포지션 생성
        for i in range(5):
            position = self._create_position(f"{i+1}번째 진입")
            if not position:
                return False
            self.logger.info(f"{i+1}번째 포지션 생성 성공")
            time.sleep(1)
        
        # 6번째 포지션 생성 시도 (실패해야 함)
        sixth_position = self._create_position("6번째 진입")
        if sixth_position:
            self.logger.error("6번째 포지션이 생성되었습니다 (실패해야 함)")
            return False
        self.logger.info("6번째 포지션 생성 실패 (예상된 결과)")
        
        # 포지션 수 확인
        mt5_positions = mt5.positions_get(symbol=self.symbol)
        if len(mt5_positions) != 5:
            self.logger.error(f"포지션 수 불일치: {len(mt5_positions)} != 5")
            return False
            
        self.logger.info("피라미딩 진입 테스트 성공")
        return True
        
    def _create_position(self, comment):
        """포지션 생성"""
        # MT5의 실제 포지션 수 확인
        mt5_positions = mt5.positions_get(symbol=self.symbol)
        current_positions = len(mt5_positions) if mt5_positions else 0
        
        if current_positions >= 4:
            self.logger.info(f"{self.symbol} 최대 유닛 수 초과: {current_positions}/4")
            return None
            
        # 현재가 확인
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            self.logger.error(f"{self.symbol} 심볼 정보 없음")
            return None
            
        # 손절가를 현재가에서 충분히 멀리 설정
        entry_price = symbol_info.ask
        stop_loss = entry_price - (symbol_info.point * 1000)  # 1000 포인트 아래
        
        # 주문 요청 생성
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": entry_price,
            "sl": stop_loss,
            "magic": self.magic,
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # 주문 실행
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"주문 실패: {result.comment}")
            return None
            
        # Position 객체 생성
        position = Position()
        position.ticket = result.order
        position.symbol = self.symbol
        position.type = 'BUY'
        position.volume = self.volume
        position.entry_price = result.price
        position.sl_price = stop_loss
        position.entry_time = datetime.utcnow()
        position.status = 'OPEN'
        
        # PositionManager에 추가
        if not self.position_manager.add_position(position):
            self.logger.error("포지션 추가 실패")
            return None
            
        self.logger.info(f"{self.symbol} BUY 포지션 추가 (티켓: {position.ticket})")
        return position
        
    def run_tests(self):
        """전체 테스트 실행"""
        try:
            # 1. 피라미딩 진입
            if not self.test_pyramid_entry():
                return
                
            self.logger.info("\n모든 테스트 완료")
            
        except Exception as e:
            self.logger.error(f"테스트 중 오류 발생: {e}")
        finally:
            self.cleanup()

def main():
    """메인 함수"""
    try:
        tester = PositionPyramidTest()
        tester.run_tests()
    except Exception as e:
        print(f"테스트 실패: {e}")
        # 에러 발생시에도 MT5 종료
        if mt5.initialize():
            mt5.shutdown()

if __name__ == '__main__':
    main() 