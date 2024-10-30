import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import time
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from core.data_feed import DataFeed

class DataFeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 시작 전 한 번만 실행"""
        if not mt5.initialize():
            raise Exception("MT5 초기화 실패")
        
        # 심볼 확인
        symbols = mt5.symbols_get()
        available_symbols = [s.name for s in symbols]
        if "#USNDAQ100" not in available_symbols:
            raise Exception("#USNDAQ100 심볼을 찾을 수 없음")
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 종료 후 한 번만 실행"""
        mt5.shutdown()
    
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        self.symbols = ["#USNDAQ100"]
        self.data_feed = DataFeed(self.symbols)
    
    def test_initialize_data(self):
        """초기 데이터 로드 테스트"""
        for symbol in self.symbols:
            df = self.data_feed.get_data(symbol)
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 60)
            self.assertTrue(self.data_feed.validate_data(symbol))
            
            # 시간 간격 확인
            time_diff = df.index.to_series().diff()[1:]
            self.assertTrue(all(td == timedelta(minutes=1) for td in time_diff))
    
    def test_update(self):
        """데이터 업데이트 테스트"""
        for symbol in self.symbols:
            initial_last_time = self.data_feed.get_data(symbol).index[-1]
            
            # 업데이트 실행
            self.data_feed.update()
            
            # 데이터 검증
            df = self.data_feed.get_data(symbol)
            self.assertIsNotNone(df)
            self.assertEqual(len(df), 60)
            self.assertTrue(self.data_feed.validate_data(symbol))
            
            # 마지막 봉 시간이 변경되었는지 확인
            current_last_time = df.index[-1]
            self.assertGreaterEqual(current_last_time, initial_last_time)
    
    def test_data_integrity(self):
        """데이터 무결성 테스트"""
        for symbol in self.symbols:
            df = self.data_feed.get_data(symbol)
            
            # 1. 시간 순서 확인
            self.assertTrue(df.index.is_monotonic_increasing)
            
            # 2. 가격 데이터 확인
            self.assertTrue(all(df['high'] >= df['low']))
            self.assertTrue(all(df['high'] >= df['open']))
            self.assertTrue(all(df['high'] >= df['close']))
            self.assertTrue(all(df['low'] <= df['open']))
            self.assertTrue(all(df['low'] <= df['close']))
            
            # 3. 시간 간격 확인
            time_diff = df.index.to_series().diff()[1:]
            self.assertTrue(all(td == timedelta(minutes=1) for td in time_diff))
    
    def test_minute_update(self):
        """1분마다 업데이트 테스트"""
        print("\n1분마다 업데이트 테스트 시작 (2분 동안 실행)")
        start_time = time.time()
        updates = []
        last_candle = None
        
        try:
            while time.time() - start_time < 120:  # 2분 동안 테스트
                for symbol in self.symbols:
                    df = self.data_feed.get_data(symbol)
                    current_candle = df.iloc[-1]
                    
                    # 새로운 봉이 추가되었는지 확인
                    if last_candle is not None and current_candle.name > last_candle.name:
                        updates.append(current_candle.name)
                        print(f"\n새로운 봉 감지: {current_candle.name}")
                        print(f"이전 봉 시간: {last_candle.name}")
                        print(f"시간 차이: {(current_candle.name - last_candle.name).total_seconds()}초")
                        print(f"마지막 봉 정보:")
                        print(f"시가: {current_candle['open']:.5f}")
                        print(f"고가: {current_candle['high']:.5f}")
                        print(f"저가: {current_candle['low']:.5f}")
                        print(f"종가: {current_candle['close']:.5f}")
                        print(f"볼륨: {current_candle['tick_volume']}")
                        
                        # 업데이트 간격이 정확히 1분인지 확인
                        if len(updates) >= 2:
                            time_diff = (updates[-1] - updates[-2]).total_seconds()
                            self.assertEqual(time_diff, 60, 
                                f"업데이트 간격이 1분이 아님: {time_diff}초")
                    
                    last_candle = current_candle
                
                # 데이터 업데이트
                self.data_feed.update()
                time.sleep(1)  # 1초 대기
                
        except KeyboardInterrupt:
            print("\n테스트 중단됨")
        
        # 최소한 1번의 업데이트는 있어야 함
        self.assertGreater(len(updates), 0, "업데이트가 발생하지 않음")
        
        # 업데이트 간격 출력
        if len(updates) >= 2:
            for i in range(1, len(updates)):
                time_diff = (updates[i] - updates[i-1]).total_seconds()
                print(f"\n업데이트 간격: {time_diff}초")
                self.assertEqual(time_diff, 60, 
                    f"업데이트 간격이 1분이 아님: {time_diff}초")

if __name__ == '__main__':
    unittest.main()