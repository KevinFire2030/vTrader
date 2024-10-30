import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
from utils.config import Config

class ConfigTest(unittest.TestCase):
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        config_path = os.path.join(project_root, "config.yaml")
        self.config = Config(config_path)
    
    def test_load_config(self):
        """설정 파일 로드 테스트"""
        self.assertIsNotNone(self.config.config_data)
        self.assertIn('system', self.config.config_data)
        self.assertIn('trading', self.config.config_data)
        self.assertIn('strategy', self.config.config_data)
        self.assertIn('mt5', self.config.config_data)
    
    def test_get_symbols(self):
        """거래 심볼 조회 테스트"""
        symbols = self.config.get_symbols()
        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)
        self.assertIn("#USNDAQ100", symbols)
    
    def test_get_risk_params(self):
        """리스크 파라미터 조회 테스트"""
        risk_params = self.config.get_risk_params()
        self.assertIsInstance(risk_params, dict)
        self.assertIn('max_units', risk_params)
        self.assertIn('max_units_per_symbol', risk_params)
        self.assertIn('risk_per_unit', risk_params)
    
    def test_get_strategy_params(self):
        """전략 파라미터 조회 테스트"""
        strategy_params = self.config.get_strategy_params()
        self.assertIsInstance(strategy_params, dict)
        self.assertIn('ema', strategy_params)
        self.assertIn('atr', strategy_params)
    
    def test_get_mt5_params(self):
        """MT5 파라미터 조회 테스트"""
        mt5_params = self.config.get_mt5_params()
        self.assertIsInstance(mt5_params, dict)
        self.assertIn('magic_number', mt5_params)
        self.assertIn('deviation', mt5_params)
        self.assertIn('filling_type', mt5_params)

if __name__ == '__main__':
    unittest.main() 