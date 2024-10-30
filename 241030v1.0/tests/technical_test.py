import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import pandas as pd
import numpy as np
from core.technical import TechnicalAnalysis

class TechnicalTest(unittest.TestCase):
    """Technical 모듈 테스트"""
    def setUp(self):
        """테스트 데이터 준비"""
        self.ta = TechnicalAnalysis()
        
        # 테스트 데이터 생성 (100개의 봉)
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        self.df = pd.DataFrame({
            'open': np.random.normal(100, 1, 100),
            'high': np.random.normal(101, 1, 100),
            'low': np.random.normal(99, 1, 100),
            'close': np.random.normal(100, 1, 100),
            'volume': np.random.normal(1000, 100, 100)
        })
        
        # high/low 값 보정
        self.df['high'] = self.df[['open', 'high', 'close']].max(axis=1)
        self.df['low'] = self.df[['open', 'low', 'close']].min(axis=1)
        
    def test_ema_calculation(self):
        """EMA 계산 테스트"""
        # 지표 계산
        df = self.ta.calculate_indicators(self.df)
        
        # EMA 컬럼 존재 확인
        self.assertIn('ema_short', df.columns)
        self.assertIn('ema_mid', df.columns)
        self.assertIn('ema_long', df.columns)
        
        # EMA 값 검증
        self.assertEqual(len(df['ema_short'].dropna()), len(df) - self.ta.ema_periods['short'] + 1)
        self.assertEqual(len(df['ema_mid'].dropna()), len(df) - self.ta.ema_periods['mid'] + 1)
        self.assertEqual(len(df['ema_long'].dropna()), len(df) - self.ta.ema_periods['long'] + 1)
        
    def test_atr_calculation(self):
        """ATR 계산 테스트"""
        # 지표 계산
        df = self.ta.calculate_indicators(self.df)
        
        # ATR 컬럼 존재 확인
        self.assertIn('atr', df.columns)
        
        # ATR 값 검증
        self.assertEqual(len(df['atr'].dropna()), len(df) - self.ta.atr_period + 1)
        self.assertTrue(all(df['atr'].dropna() > 0))  # ATR은 항상 양수
        
    def test_entry_signal(self):
        """진입 신호 테스트"""
        # 지표 계산
        df = self.ta.calculate_indicators(self.df)
        
        # 정배열 상태 만들기
        df.loc[df.index[-1], 'ema_short'] = 101
        df.loc[df.index[-1], 'ema_mid'] = 100
        df.loc[df.index[-1], 'ema_long'] = 99
        
        # 롱 진입 신호 확인
        signal = self.ta.check_entry_signal(df)
        self.assertEqual(signal, 'BUY')
        
        # 역배열 상태 만들기
        df.loc[df.index[-1], 'ema_short'] = 99
        df.loc[df.index[-1], 'ema_mid'] = 100
        df.loc[df.index[-1], 'ema_long'] = 101
        
        # 숏 진입 신호 확인
        signal = self.ta.check_entry_signal(df)
        self.assertEqual(signal, 'SELL')
        
    def test_close_signal(self):
        """청산 신호 테스트"""
        # 지표 계산
        df = self.ta.calculate_indicators(self.df)
        
        # 롱 포지션 청산 조건 만들기
        df.loc[df.index[-1], 'ema_short'] = 99
        df.loc[df.index[-1], 'ema_mid'] = 100
        
        # 롱 포지션 청산 신호 확인
        should_close = self.ta.check_close_signal(df, 'BUY')
        self.assertTrue(should_close)
        
        # 숏 포지션 청산 조건 만들기
        df.loc[df.index[-1], 'ema_short'] = 101
        df.loc[df.index[-1], 'ema_mid'] = 100
        
        # 숏 포지션 청산 신호 확인
        should_close = self.ta.check_close_signal(df, 'SELL')
        self.assertTrue(should_close)
        
    def test_min_data_requirement(self):
        """최소 데이터 요구사항 테스트"""
        # 최소 데이터 개수보다 적은 데이터
        small_df = self.df.head(self.ta.min_periods - 1)
        
        # 지표 계산
        df = self.ta.calculate_indicators(small_df)
        
        # 원본 데이터가 변경되지 않았는지 확인
        self.assertEqual(len(df), len(small_df))
        
        # 진입/청산 신호가 None/False를 반환하는지 확인
        self.assertIsNone(self.ta.check_entry_signal(df))
        self.assertFalse(self.ta.check_close_signal(df, 'BUY'))
        self.assertFalse(self.ta.check_close_signal(df, 'SELL'))

if __name__ == '__main__':
    unittest.main() 