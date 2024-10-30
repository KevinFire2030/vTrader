import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

def calculate_atr(symbol, timeframe, period=14):
    # MT5에서 가격 데이터 가져오기
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period * 2)
    df = pd.DataFrame(rates)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('datetime', inplace=True)
    
    # pandas_ta를 사용하여 ATR 계산
    atr = ta.atr(df['high'], df['low'], df['close'], length=period, mamode='ema')
    
    return atr.iloc[-1]

def get_visible_symbols():
    symbols = mt5.symbols_get()
    visible_symbols = [symbol.name for symbol in symbols if symbol.visible]
    return visible_symbols

def get_symbol_info(symbol, timeframe, period=14):
    # ATR 계산
    atr = calculate_atr(symbol, timeframe, period)
    
    # 심볼 정보 가져오기
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"심볼 {symbol}에 대한 정보를 가져올 수 없습니다.")
        return None
    
    # 거래 데이터 가져오기
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
    df = pd.DataFrame(rates)
    
    # 거래 대금 계산 (real_volume * close)
    df['turnover'] = df['real_volume'] * df['close']
    avg_turnover = df['turnover'].mean()
    avg_tick_volume = df['tick_volume'].mean()
    avg_real_volume = df['real_volume'].mean()
    
    return {
        'symbol': symbol,
        'atr': atr,
        'avg_turnover': avg_turnover,
        'avg_tick_volume': avg_tick_volume,
        'avg_real_volume': avg_real_volume,
        'point': symbol_info.point,
        'trade_contract_size': symbol_info.trade_contract_size
    }

def rank_symbols_by_liquidity_and_volatility(timeframe, period=14):
    visible_symbols = get_visible_symbols()
    symbol_info_list = []
    
    for symbol in visible_symbols:
        info = get_symbol_info(symbol, timeframe, period)
        if info is not None:
            symbol_info_list.append(info)
    
    # 유동성(거래 대금)과 변동성(ATR)에 따라 정렬
    sorted_symbols = sorted(symbol_info_list, key=lambda x: (x['avg_turnover'], x['atr']), reverse=True)
    
    return sorted_symbols

# 사용 예시
if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 초기화 실패")
        mt5.shutdown()
    
    ranked_symbols = rank_symbols_by_liquidity_and_volatility(mt5.TIMEFRAME_H1, period=14)
    
    print("Watch List 심볼 (유동성과 변동성이 높은 순):")
    for info in ranked_symbols:
        print(f"심볼: {info['symbol']}")
        print(f"평균 거래 대금: {info['avg_turnover']:.2f}")
        print(f"ATR: {info['atr']:.5f}")
        print(f"평균 틱 볼륨: {info['avg_tick_volume']:.2f}")
        print(f"평균 실제 거래량: {info['avg_real_volume']:.2f}")
        print(f"포인트: {info['point']:.5f}")
        print(f"계약 크기: {info['trade_contract_size']:.2f}")
        print("---")
    
    mt5.shutdown()
