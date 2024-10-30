import sys
import os

# 현재 스크립트의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
mt5_backtrader_path = os.path.join(project_root, 'mt5_backtrader')
sys.path.insert(0, mt5_backtrader_path)

import backtrader as bt
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from live_strategy import LiveStrategy

def get_watchlist_symbols():
    """MT5의 Market Watch에서 visible한 심볼들을 가져오는 함수"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return []
    
    symbols = []
    for symbol in mt5.symbols_get():
        if symbol.visible and len(symbols) < 10:
            symbols.append(symbol.name)
    
    mt5.shutdown()
    print(f"Market Watch에서 visible한 심볼: {symbols}")
    return symbols

def get_current_bars(symbols):
    """현재 시간 기준 60개의 1분봉 데이터 가져오기"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    current_time = mt5.symbol_info_tick(symbols[0]).time
    from_time = current_time - (60 * 60)  # 60분을 초 단위로 계산

    data_dict = {}
    for symbol in symbols:
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, from_time, current_time)
        
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            print(f"\n{symbol} 데이터:")
            print(f"데이터 개수: {len(df)}")
            print(f"시작: {df.index[0]}")
            print(f"종료: {df.index[-1]}")
            
            data_dict[symbol] = df
        else:
            print(f"\n{symbol} 데이터 없음")

    mt5.shutdown()
    return data_dict

if __name__ == '__main__':
    symbols = get_watchlist_symbols()
    
    if symbols:
        data_dict = get_current_bars(symbols)
        
        if data_dict:
            print("\n=== 전체 데이터 요약 ===")
            for symbol, df in data_dict.items():
                print(f"\n{symbol}:")
                print(df.head())
                print("...")
                print(df.tail())
