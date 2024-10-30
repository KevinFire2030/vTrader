import MetaTrader5 as mt5
import pandas as pd

def get_active_symbols():
    symbols = mt5.symbols_get()
    active_symbols = []
    for symbol in symbols:
        if symbol.visible:
            symbol_info = mt5.symbol_info(symbol.name)
            if symbol_info is not None and symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                active_symbols.append(symbol.name)
    return active_symbols

def get_volume_data(timeframe=mt5.TIMEFRAME_M1, period=1):
    active_symbols = get_active_symbols()
    volume_data = []

    for symbol in active_symbols:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
        if rates is not None and len(rates) > 0:
            volume_data.append({
                'symbol': symbol,
                'tick_volume': rates[0]['tick_volume'],
                'real_volume': rates[0]['real_volume']
            })

    return pd.DataFrame(volume_data)

def print_volume_diff():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    df = get_volume_data()
    print(df)

    mt5.shutdown()

if __name__ == "__main__":
    print_volume_diff()
