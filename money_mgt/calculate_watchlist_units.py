import sys
import os
import time
import MetaTrader5 as mt5
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# 현재 스크립트의 디렉토리를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from money_mgt.turtle_units import calculate_turtle_units
from money_mgt.atr import calculate_atr

def initialize_mt5():
    if not mt5.initialize():
        print(f"MetaTrader5 초기화 실패, 에러 코드 = {mt5.last_error()}")
        return False
    return True

def get_watchlist_symbols():
    watchlist = mt5.symbols_get()
    valid_symbols = []
    for symbol in watchlist:
        if symbol.visible:
            symbol_info = mt5.symbol_info(symbol.name)
            if symbol_info is not None:
                valid_symbols.append((symbol.name, symbol_info))
    print(f"가져온 유효한 심볼 수: {len(valid_symbols)}")
    return valid_symbols

def calculate_spread_in_dollars(symbol_info):
    spread_points = symbol_info.spread
    tick_size = symbol_info.trade_tick_size
    tick_value = symbol_info.trade_tick_value
    spread_dollars = (spread_points * tick_value) / (1 / tick_size)
    return spread_dollars

def calculate_watchlist_units(account_value, risk_percent):
    if not initialize_mt5():
        return None

    results = []
    symbols = get_watchlist_symbols()
    
    for symbol, symbol_info in symbols:
        print(f"\n처리 중인 심볼: {symbol}")
        units, atr, actual_risk = calculate_turtle_units(symbol, account_value, risk_percent)
        
        if units is not None:
            spread_dollars = calculate_spread_in_dollars(symbol_info)
            results.append({
                'Symbol': symbol,
                'Units': units,
                'ATR': atr,
                'Tick Value': symbol_info.trade_tick_value,
                'Tick Size': symbol_info.trade_tick_size,
                'Min Volume': symbol_info.volume_min,
                'Risk': actual_risk,
                'Risk Amount': account_value * actual_risk,
                'Spread (points)': symbol_info.spread,
                'Spread ($)': spread_dollars
            })
            print(f"{symbol} 처리 완료")
        else:
            print(f"{symbol} 처리 실패")

    mt5.shutdown()
    return pd.DataFrame(results)

def save_to_excel(df, filename):
    if df is None or df.empty:
        print("저장할 데이터가 없습니다.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "WatchList Units"

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    try:
        wb.save(filename)
        print(f"결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    account_value = 100  # 계좌 가치 $100
    risk_percent = 0.01  # 1% 리스크
    filename = "WatchList_Units.xlsx"

    df = calculate_watchlist_units(account_value, risk_percent)
    if df is not None and not df.empty:
        print(f"\n총 처리된 심볼 수: {len(df)}")
        save_to_excel(df, filename)
    else:
        print("계산 실패 또는 데이터가 비어있습니다.")
