import pandas as pd
import pandas_ta as ta
from typing import Optional

class TechnicalAnalysis:
    """기술적 분석"""
    def __init__(self):
        # EMA 설정
        self.ema_periods = {
            'short': 5,
            'mid': 20,
            'long': 40
        }
        
        # ATR 설정
        self.atr_period = 20
        self.atr_mamode = 'ema'  # EMA 방식으로 계산
        
        # 최소 필요 데이터 수
        self.min_periods = 40
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """지표 계산"""
        if len(df) < self.min_periods:
            return df
            
        # EMA 계산
        df['ema_short'] = ta.ema(df['close'], length=self.ema_periods['short'])
        df['ema_mid'] = ta.ema(df['close'], length=self.ema_periods['mid'])
        df['ema_long'] = ta.ema(df['close'], length=self.ema_periods['long'])
        
        # ATR 계산 (EMA 방식)
        df['atr'] = ta.atr(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            length=self.atr_period,
            mamode=self.atr_mamode  # EMA 방식 적용
        )
        
        return df
        
    def check_entry_signal(self, df: pd.DataFrame) -> Optional[str]:
        """진입 신호 확인"""
        if len(df) < self.min_periods:
            return None
            
        # 마지막 봉 기준
        last = df.iloc[-1]
        
        # 정배열 확인 (롱 진입)
        if (last['ema_short'] > last['ema_mid'] > last['ema_long']):
            return 'BUY'
            
        # 역배열 확인 (숏 진입)
        if (last['ema_short'] < last['ema_mid'] < last['ema_long']):
            return 'SELL'
            
        return None
        
    def check_close_signal(self, df: pd.DataFrame, position_type: str) -> bool:
        """청산 신호 확인"""
        if len(df) < self.min_periods:
            return False
            
        # 마지막 봉 기준
        last = df.iloc[-1]
        
        # 롱 포지션 청산
        if position_type == 'BUY':
            return last['ema_short'] < last['ema_mid']
            
        # 숏 포지션 청산
        if position_type == 'SELL':
            return last['ema_short'] > last['ema_mid']
            
        return False