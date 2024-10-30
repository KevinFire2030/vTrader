import yaml
import os
from typing import Dict, List, Any

class Config:
    """설정 관리"""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_data = {}
        self._load_config()
        self._validate_config()
        
    def _load_config(self):
        """YAML 설정 파일 로드"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없음: {self.config_path}")
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config_data = yaml.safe_load(f)
            
    def _validate_config(self):
        """설정값 검증"""
        required_sections = ['system', 'trading', 'strategy', 'mt5']
        for section in required_sections:
            if section not in self.config_data:
                raise ValueError(f"필수 설정 섹션 없음: {section}")
                
        # 시스템 설정 검증
        system = self.config_data['system']
        if 'mode' not in system or system['mode'] not in ['live', 'test', 'backtest']:
            raise ValueError("올바른 시스템 모드가 설정되지 않음")
            
        # 거래 설정 검증
        trading = self.config_data['trading']
        if 'symbols' not in trading or not trading['symbols']:
            raise ValueError("거래 심볼이 설정되지 않음")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return self.config_data.get(section, {}).get(key, default)
        
    def get_symbols(self) -> List[str]:
        """거래 심볼 목록 조회"""
        return self.config_data['trading']['symbols']
        
    def get_log_path(self) -> str:
        """로그 경로 조회"""
        return self.config_data['system']['log_path']
        
    def get_risk_params(self) -> Dict:
        """리스크 관리 파라미터 조회"""
        trading = self.config_data['trading']
        return {
            'max_units': trading.get('max_units', 15),
            'max_units_per_symbol': trading.get('max_units_per_symbol', 4),
            'risk_per_unit': trading.get('risk_per_unit', 0.01)
        }
        
    def get_strategy_params(self) -> Dict:
        """전략 파라미터 조회"""
        strategy = self.config_data['strategy']
        return {
            'ema': strategy.get('ema', {'short': 5, 'mid': 20, 'long': 40}),
            'atr': strategy.get('atr', {'period': 20, 'sl_multiple': 2.0})
        }
        
    def get_mt5_params(self) -> Dict:
        """MT5 파라미터 조회"""
        mt5 = self.config_data['mt5']
        return {
            'magic_number': mt5.get('magic_number', 241030),
            'deviation': mt5.get('deviation', 20),
            'filling_type': mt5.get('filling_type', 'IOC')
        }