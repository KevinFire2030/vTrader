import MetaTrader5 as mt5
import pandas as pd

def get_trade_calc_modes():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # Market Watch에 있는 심볼 가져오기
    symbols = mt5.symbols_get()
    visible_symbols = [symbol for symbol in symbols if symbol.visible]

    # 각 심볼의 trade_calc_mode 가져오기
    calc_modes = []
    for symbol in visible_symbols:
        symbol_info = mt5.symbol_info(symbol.name)
        if symbol_info is not None:
            calc_modes.append({
                'symbol': symbol.name,
                'trade_calc_mode': symbol_info.trade_calc_mode
            })

    mt5.shutdown()

    return pd.DataFrame(calc_modes)

def print_trade_calc_modes():
    df = get_trade_calc_modes()
    if df is not None:
        # trade_calc_mode에 대한 설명 딕셔너리
        mode_descriptions = {
            0: "SYMBOL_CALC_MODE_FOREX",
            1: "SYMBOL_CALC_MODE_FUTURES",
            2: "SYMBOL_CALC_MODE_CFD",
            3: "SYMBOL_CALC_MODE_CFDINDEX",
            4: "SYMBOL_CALC_MODE_CFDLEVERAGE",
            32: "SYMBOL_CALC_MODE_EXCH_STOCKS",
            33: "SYMBOL_CALC_MODE_EXCH_FUTURES",
            34: "SYMBOL_CALC_MODE_EXCH_FUTURES_FORTS"
        }

        # 결과 출력
        for _, row in df.iterrows():
            mode = row['trade_calc_mode']
            description = mode_descriptions.get(mode, "Unknown")
            print(f"심볼: {row['symbol']}, trade_calc_mode: {mode} ({description})")

if __name__ == "__main__":
    print_trade_calc_modes()
