import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pandas_ta as ta

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    return True

def get_historical_data(symbol, timeframe, start_date, end_date):
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    rates = mt5.copy_rates_range(symbol, timeframe, start_timestamp, end_timestamp)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    print(f"데이터 로드: {len(df)} 개의 캔들")
    return df

def calculate_atr(df, period=20):
    atr = ta.atr(df['high'], df['low'], df['close'], length=period, mamode='ema')
    print(f"ATR 범위: {atr.min()} - {atr.max()}")
    return atr

def turtle_strategy(df, atr_period=20, risk_percent=0.01, account_value=10000):
    df['atr'] = calculate_atr(df, atr_period)
    df['entry_long'] = df['high'].rolling(window=20).max()
    df['entry_short'] = df['low'].rolling(window=20).min()
    df['exit_long'] = df['low'].rolling(window=10).min()
    df['exit_short'] = df['high'].rolling(window=10).max()
    
    position = 0
    entry_price = 0
    stop_loss = 0
    
    trades = []
    
    for i in range(len(df)):
        if position == 0:
            if df['close'].iloc[i] > df['entry_long'].iloc[i]:
                position = 1
                entry_price = df['close'].iloc[i]
                stop_loss = entry_price - 2 * df['atr'].iloc[i]
                dollar_volatility = df['atr'].iloc[i]
                position_size = (account_value * risk_percent) / dollar_volatility
                trades.append({'date': df['time'].iloc[i], 'type': 'buy', 'price': entry_price, 'size': position_size})
                print(f"매수 진입: 날짜 {df['time'].iloc[i]}, 가격 {entry_price}, 크기 {position_size}")
            elif df['close'].iloc[i] < df['entry_short'].iloc[i]:
                position = -1
                entry_price = df['close'].iloc[i]
                stop_loss = entry_price + 2 * df['atr'].iloc[i]
                dollar_volatility = df['atr'].iloc[i]
                position_size = (account_value * risk_percent) / dollar_volatility
                trades.append({'date': df['time'].iloc[i], 'type': 'sell', 'price': entry_price, 'size': position_size})
                print(f"매도 진입: 날짜 {df['time'].iloc[i]}, 가격 {entry_price}, 크기 {position_size}")
        elif position == 1:
            if df['close'].iloc[i] < df['exit_long'].iloc[i] or df['close'].iloc[i] < stop_loss:
                position = 0
                exit_price = df['close'].iloc[i]
                trades.append({'date': df['time'].iloc[i], 'type': 'sell', 'price': exit_price, 'size': position_size})
                print(f"매수 청산: 날짜 {df['time'].iloc[i]}, 가격 {exit_price}")
        elif position == -1:
            if df['close'].iloc[i] > df['exit_short'].iloc[i] or df['close'].iloc[i] > stop_loss:
                position = 0
                exit_price = df['close'].iloc[i]
                trades.append({'date': df['time'].iloc[i], 'type': 'buy', 'price': exit_price, 'size': position_size})
                print(f"매도 청산: 날짜 {df['time'].iloc[i]}, 가격 {exit_price}")
    
    return trades

def backtest(symbol, timeframe, start_date, end_date):
    if not initialize_mt5():
        return
    
    df = get_historical_data(symbol, timeframe, start_date, end_date)
    trades = turtle_strategy(df)
    
    # 성과 분석
    total_profit = 0
    winning_trades = 0
    losing_trades = 0
    
    for i in range(0, len(trades), 2):
        if i+1 < len(trades):
            entry = trades[i]
            exit = trades[i+1]
            if entry['type'] == 'buy':
                profit = (exit['price'] - entry['price']) * entry['size']
            else:
                profit = (entry['price'] - exit['price']) * entry['size']
            
            total_profit += profit
            if profit > 0:
                winning_trades += 1
            else:
                losing_trades += 1
    
    print(f"총 수익: ${total_profit:.2f}")
    total_trades = winning_trades + losing_trades
    if total_trades > 0:
        win_rate = (winning_trades / total_trades) * 100
        print(f"승률: {win_rate:.2f}%")
    else:
        print("거래가 없습니다.")
    print(f"총 거래 횟수: {total_trades}")
    
    mt5.shutdown()

if __name__ == "__main__":
    symbol = "EURUSD"
    timeframe = mt5.TIMEFRAME_D1  # 일봉으로 변경
    start_date = datetime(2022, 1, 1)  # 시작 날짜를 1년 앞당김
    end_date = datetime(2023, 12, 31)
    
    backtest(symbol, timeframe, start_date, end_date)
