import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import time
from datetime import datetime, timedelta
from core.position import Position, PositionManager

class PositionTest(unittest.TestCase):
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        self.position = Position()
        self.position.ticket = 12345
        self.position.symbol = "#USNDAQ100"
        self.position.type = 'BUY'
        self.position.volume = 1.0
        self.position.entry_price = 15000.0
        self.position.sl_price = 14900.0
        self.position.entry_time = datetime.utcnow()
        self.position.entry_atr = 50.0
        self.position.status = 'OPEN'
        
    def test_position_validation(self):
        """데이터 검증 테스트"""
        # 유효한 포지션
        self.assertTrue(self.position.validate())
        
        # 필수 데이터 누락
        invalid_position = Position()
        self.assertFalse(invalid_position.validate())
        
        # 잘못된 타입
        self.position.type = 'INVALID'
        self.assertFalse(self.position.validate())
        
        # 잘못된 볼륨
        self.position.type = 'BUY'
        self.position.volume = -1.0
        self.assertFalse(self.position.validate())
        
        # 잘못된 가격
        self.position.volume = 1.0
        self.position.entry_price = -15000.0
        self.assertFalse(self.position.validate())
        
    def test_position_status(self):
        """포지션 상태 테스트"""
        # 초기 상태
        self.assertTrue(self.position.is_long())
        self.assertFalse(self.position.is_short())
        self.assertTrue(self.position.is_open())
        self.assertFalse(self.position.is_closed())
        
        # 포지션 청산
        self.position.close(15100.0, datetime.utcnow())
        self.assertFalse(self.position.is_open())
        self.assertTrue(self.position.is_closed())
        self.assertEqual(self.position.status, 'CLOSED')
        
    def test_position_profit(self):
        """손익 계산 테스트"""
        # 미실현 손익
        self.position.update_state(15050.0)
        self.assertEqual(self.position.upnl, 50.0)  # (15050 - 15000) * 1.0
        
        # 수수료 반영
        self.position.commission = 2.0
        self.position.update_state(15050.0)
        self.assertEqual(self.position.upnl, 48.0)  # 50 - 2
        
        # 실현 손익
        self.position.close(15100.0, datetime.utcnow())
        self.assertEqual(self.position.profit, 98.0)  # (15100 - 15000) * 1.0 - 2
        
    def test_position_risk(self):
        """리스크 계산 테스트"""
        # 리스크 금액
        risk = self.position.get_risk_amount()
        self.assertEqual(risk, 100.0)  # (15000 - 14900) * 1.0
        
        # 최대 손실
        max_loss = self.position.get_max_loss()
        self.assertEqual(max_loss, 100.0)
        
        # 최대 이익
        self.position.update_state(15100.0)
        max_profit = self.position.get_max_profit()
        self.assertEqual(max_profit, 100.0)
        
    def test_position_time(self):
        """시간 관리 테스트"""
        # 보유 시간
        time.sleep(1)
        holding_time = self.position.get_holding_time()
        self.assertGreater(holding_time.total_seconds(), 0)
        
        # 청산 후 보유 시간
        exit_time = datetime.utcnow() + timedelta(hours=1)
        self.position.close(15100.0, exit_time)
        self.assertEqual(self.position.lifetime, exit_time - self.position.entry_time)

class PositionManagerTest(unittest.TestCase):
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        self.manager = PositionManager()
        self.symbol = "#USNDAQ100"
        
        # 테스트용 포지션 생성 (필수 속성 추가)
        self.position = Position()
        self.position.ticket = 12345
        self.position.symbol = self.symbol
        self.position.type = 'BUY'
        self.position.volume = 1.0
        self.position.entry_price = 15000.0
        self.position.sl_price = 14900.0
        self.position.entry_time = datetime.utcnow()
        self.position.status = 'OPEN'
        self.position.entry_atr = 50.0
        
    def test_position_limits(self):
        """포지션 한도 테스트"""
        # 첫 번째 포지션 추가
        self.assertTrue(self.manager.add_position(self.position))
        self.assertEqual(self.manager.total_units, 1)
        
        # 심볼당 최대 유닛 테스트
        for i in range(3):  # 이미 1개가 있으므로 3개 더 추가
            position = Position()
            position.ticket = 12346 + i
            position.symbol = self.symbol
            position.type = 'BUY'
            position.volume = 1.0
            position.entry_price = 15000.0
            position.sl_price = 14900.0
            position.entry_time = datetime.utcnow()
            position.status = 'OPEN'
            position.entry_atr = 50.0
            self.assertTrue(self.manager.add_position(position))
            
        # 5번째 포지션은 추가 실패해야 함
        position = Position()
        position.ticket = 12350
        position.symbol = self.symbol
        position.type = 'BUY'
        position.volume = 1.0
        position.entry_price = 15000.0
        position.sl_price = 14900.0
        position.entry_time = datetime.utcnow()
        position.status = 'OPEN'
        position.entry_atr = 50.0
        self.assertFalse(self.manager.add_position(position))
        
    def test_position_management(self):
        """포지션 관리 테스트"""
        # 포지션 추가
        self.assertTrue(self.manager.add_position(self.position))
        positions = self.manager.get_positions(self.symbol)
        self.assertEqual(len(positions), 1)
        
        # 손절가 수정
        new_sl = 14950.0
        self.assertTrue(self.manager.update_sl(self.symbol, self.position.ticket, new_sl))
        position = self.manager.get_positions(self.symbol)[0]
        self.assertEqual(position.sl_price, new_sl)
        
        # 포지션 청산
        exit_time = datetime.utcnow()
        self.assertTrue(self.manager.close_position(
            self.symbol,
            self.position.ticket,
            15100.0,
            exit_time
        ))
        
        # 청산 결과 확인
        self.assertEqual(len(self.manager.get_positions(self.symbol)), 0)
        self.assertEqual(len(self.manager.closed_positions), 1)
        self.assertEqual(self.manager.total_units, 0)
        
    def test_profit_calculation(self):
        """손익 계산 테스트"""
        # 포지션 추가
        self.manager.add_position(self.position)
        
        # 미실현 손익 업데이트
        self.position.update_state(15100.0)
        total_profit = self.manager.get_total_profit()
        self.assertEqual(total_profit, 100.0)

if __name__ == '__main__':
    unittest.main() 