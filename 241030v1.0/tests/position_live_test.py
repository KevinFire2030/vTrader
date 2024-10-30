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

class PositionLiveTest:
    """Position 모듈 라이브 테스트"""
    def __init__(self):
        # MT5 초기화
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
            
        # 테스트 설정
        self.symbol = "#USNDAQ100"
        self.volume = 0.1
        self.magic = 241030
        
        # 모듈 초기화
        self.mt5 = MT5Wrapper()
        self.logger = Logger("logs", "position_test")
        self.position_manager = PositionManager(self.mt5, self.logger)
        
        self.logger.info("Position 라이브 테스트 시작")
        
    def cleanup(self):
        """종료 처리"""
        self.logger.info("테스트 종료")
        mt5.shutdown()
        
    def test_position_creation(self):
        """포지션 생성 테스트"""
        self.logger.info("\n=== 포지션 생성 테스트 ===")
        
        # 현재가 확인
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            self.logger.error(f"{self.symbol} 심볼 정보 없음")
            return False
            
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
            "comment": "position test",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # 주문 실행
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"주문 실패: {result.comment}")
            return False
            
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
            return False
            
        self.logger.info(f"포지션 생성 성공 (티켓: {position.ticket})")
        return True
        
    def test_position_modification(self):
        """포지션 수정 테스트"""
        self.logger.info("\n=== 포지션 수정 테스트 ===")
        
        positions = self.position_manager.get_positions(self.symbol)
        if not positions:
            self.logger.error("수정할 포지션 없음")
            return False
            
        position = positions[0]
        new_sl = position.entry_price - (mt5.symbol_info(self.symbol).point * 1500)  # 1500 포인트 아래
        
        # MT5 손절가 수정
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": self.symbol,
            "position": position.ticket,
            "sl": new_sl,
            "magic": self.magic
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"손절가 수정 실패: {result.comment}")
            return False
            
        # Position Manager 업데이트
        if not self.position_manager.update_sl(self.symbol, position.ticket, new_sl):
            self.logger.error("Position Manager 업데이트 실패")
            return False
            
        self.logger.info(f"손절가 수정 성공: {new_sl}")
        return True
        
    def test_position_closure(self):
        """포지션 청산 테스트"""
        self.logger.info("\n=== 포지션 청산 테스트 ===")
        
        positions = self.position_manager.get_positions(self.symbol)
        if not positions:
            self.logger.error("청산할 포지션 없음")
            return False
            
        position = positions[0]
        symbol_info = mt5.symbol_info(self.symbol)
        
        # 청산 주문
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "position": position.ticket,
            "price": symbol_info.bid,
            "magic": self.magic,
            "comment": "position test close",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"청산 실패: {result.comment}")
            return False
            
        # Position Manager 업데이트
        if not self.position_manager.close_position(
            self.symbol,
            position.ticket,
            result.price,
            datetime.utcnow()
        ):
            self.logger.error("Position Manager 청산 업데이트 실패")
            return False
            
        self.logger.info(f"포지션 청산 성공 (수익: {result.price - position.entry_price})")
        return True
        
    def run_tests(self):
        """전체 테스트 실행"""
        try:
            # 1. 포지션 생성
            if not self.test_position_creation():
                return
            time.sleep(1)
            
            # 2. 손절가 수정
            if not self.test_position_modification():
                return
            time.sleep(1)
            
            # 3. 포지션 청산
            if not self.test_position_closure():
                return
                
            self.logger.info("\n모든 테스트 완료")
            
        except Exception as e:
            self.logger.error(f"테스트 중 오류 발생: {e}")
        finally:
            self.cleanup()

def main():
    """메인 함수"""
    try:
        tester = PositionLiveTest()
        tester.run_tests()
    except Exception as e:
        print(f"테스트 실패: {e}")

if __name__ == '__main__':
    main() 