import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import MetaTrader5 as mt5
from utils.mt5_wrapper import MT5Wrapper

class MT5WrapperTest(unittest.TestCase):
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        self.mt5 = MT5Wrapper()
        self.symbol = "#USNDAQ100"
        
    def tearDown(self):
        """각 테스트 메서드 실행 후에 실행"""
        self.mt5.shutdown()
        
    def test_initialize(self):
        """초기화 테스트"""
        self.assertTrue(self.mt5.initialize())
        self.assertTrue(self.mt5.initialized)
        
    def test_get_server_time(self):
        """서버 시간 조회 테스트"""
        server_time = self.mt5.get_server_time()
        self.assertIsNotNone(server_time)
        self.assertIsInstance(server_time, float)
        
    def test_get_candles(self):
        """봉 데이터 조회 테스트"""
        candles = self.mt5.get_candles(self.symbol, mt5.TIMEFRAME_M1, 10)
        self.assertIsNotNone(candles)
        self.assertEqual(len(candles), 10)
        
    def test_get_positions(self):
        """포지션 조회 테스트"""
        positions = self.mt5.get_positions()
        self.assertIsInstance(positions, list)
        
    def test_connection_recovery(self):
        """연결 복구 테스트"""
        self.mt5.shutdown()
        self.assertFalse(self.mt5.initialized)
        self.assertTrue(self.mt5.check_connection())
        self.assertTrue(self.mt5.initialized)

if __name__ == '__main__':
    unittest.main() 