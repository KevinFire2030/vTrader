import MetaTrader5 as mt5
import pandas as pd
import numpy as np

def calculate_adx_and_di(symbol, timeframe, period=14):
    # MT5에서 가격 데이터 가져오기
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period * 2)
    if rates is None or len(rates) < period * 2:
        return None, None, None
    
    df = pd.DataFrame(rates)
    df['date'] = pd.to_datetime(df['time'], unit='s')
    
    # True Range 계산
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = np.abs(df['high'] - df['close'].shift())
    df['low_close'] = np.abs(df['low'] - df['close'].shift())
    df['tr'] = np.max(df[['high_low', 'high_close', 'low_close']], axis=1)
    
    # +DM, -DM 계산
    df['up_move'] = df['high'] - df['high'].shift()
    df['down_move'] = df['low'].shift() - df['low']
    df['+dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
    df['-dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
    
    # TR14, +DM14, -DM14 계산
    df['tr14'] = df['tr'].rolling(window=period).sum()
    df['+dm14'] = df['+dm'].rolling(window=period).sum()
    df['-dm14'] = df['-dm'].rolling(window=period).sum()
    
    # +DI, -DI 계산
    df['+di'] = 100 * df['+dm14'] / df['tr14']
    df['-di'] = 100 * df['-dm14'] / df['tr14']
    
    # DX 계산
    df['dx'] = 100 * np.abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    
    # ADX 계산
    df['adx'] = df['dx'].rolling(window=period).mean()
    
    return df['adx'].iloc[-1], df['+di'].iloc[-1], df['-di'].iloc[-1]

def get_active_symbols():
    symbols = mt5.symbols_get()
    active_symbols = []
    for symbol in symbols:
        if symbol.visible:
            tick = mt5.symbol_info_tick(symbol.name)
            if tick is not None and tick.last != 0:
                active_symbols.append(symbol.name)
    return active_symbols

def determine_trend(plus_di, minus_di):
    if plus_di is None or minus_di is None:
        return "데이터 없음"
    if plus_di > minus_di:
        return "상승"
    elif minus_di > plus_di:
        return "하락"
    else:
        return "중립"

def rank_symbols_by_adx(timeframe, period=14):
    active_symbols = get_active_symbols()
    symbol_adx_list = []
    
    for symbol in active_symbols:
        adx, plus_di, minus_di = calculate_adx_and_di(symbol, timeframe, period)
        if adx is not None:
            trend = determine_trend(plus_di, minus_di)
            symbol_adx_list.append({
                'symbol': symbol, 
                'adx': adx, 
                'plus_di': plus_di, 
                'minus_di': minus_di, 
                'trend': trend
            })
        else:
            print(f"심볼 {symbol}에 대한 데이터를 가져올 수 없습니다.")
    
    # ADX에 따라 정렬
    sorted_symbols = sorted(symbol_adx_list, key=lambda x: x['adx'], reverse=True)
    
    return sorted_symbols

# 사용 예시
if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 초기화 실패")
        mt5.shutdown()
    
    ranked_symbols = rank_symbols_by_adx(mt5.TIMEFRAME_M1, period=14)
    
    print("활성 Watch List 심볼 (ADX가 높은 순):")
    for info in ranked_symbols:
        print(f"심볼: {info['symbol']}, ADX: {info['adx']:.2f}, +DI: {info['plus_di']:.2f}, -DI: {info['minus_di']:.2f}, 추세: {info['trend']}")
    
    mt5.shutdown()
