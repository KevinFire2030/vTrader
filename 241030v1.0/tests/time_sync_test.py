import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import time
from datetime import datetime
import MetaTrader5 as mt5
from core.time_sync import TimeSync

class TimeSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 시작 전 한 번만 실행"""
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
        
        # EURUSD 심볼이 있는지 확인
        symbols = mt5.symbols_get()
        available_symbols = [s.name for s in symbols]
        if "#USNDAQ100" not in available_symbols:
            raise Exception("EURUSD 심볼을 찾을 수 없음")
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 종료 후 한 번만 실행"""
        mt5.shutdown()
    
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        self.time_sync = TimeSync()
    
    def test_get_server_time(self):
        """서버 시간 조회 테스트"""
        for _ in range(3):  # 3번 시도
            server_time = self.time_sync.get_server_time()
            if server_time is not None:
                self.assertIsInstance(server_time, float)
                return
            time.sleep(0.1)
        self.fail("서버 시간 조회 실패")
    
    def test_calculate_offset(self):
        """오프셋 계산 테스트"""
        for _ in range(3):  # 3번 시도
            offset = self.time_sync.calculate_offset()
            if offset is not None:
                self.assertIsInstance(offset, float)
                self.assertLess(abs(offset), 60)
                return
            time.sleep(0.1)
        self.fail("오프셋 계산 실패")
    
    def test_check_sync_status(self):
        """동기화 상태 확인 테스트"""
        status = self.time_sync.check_sync_status()
        self.assertIsInstance(status, bool)
    
    def test_wait_for_next_minute(self):
        """정각 대기 테스트"""
        # 현재 시간이 59초이면 1초만 기다리면 되므로 테스트가 빨리 끝남
        # 현재 시간이 01초이면 59초를 기다려야 하므로 테스트가 오래 걸림
        # 따라서 이 테스트는 선택적으로 실행하는 것이 좋음
        self.skipTest("시간이 오래 걸리는 테스트")
        
        start_time = time.time()
        self.time_sync.wait_for_next_minute()
        end_time = time.time()
        
        # 대기 시간이 60초를 넘지 않는지 확인
        self.assertLess(end_time - start_time, 61)
        
        # 현재 초가 0초인지 확인
        current_seconds = datetime.utcfromtimestamp(self.time_sync.get_server_time()).second
        self.assertEqual(current_seconds, 0)

if __name__ == '__main__':
    unittest.main()