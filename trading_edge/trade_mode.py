import MetaTrader5 as mt5
import pandas as pd

def get_trade_modes():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # Market Watch에 있는 심볼 가져오기
    symbols = mt5.symbols_get()
    visible_symbols = [symbol for symbol in symbols if symbol.visible]

    # 각 심볼의 trade_mode 가져오기
    trade_modes = []
    for symbol in visible_symbols:
        symbol_info = mt5.symbol_info(symbol.name)
        if symbol_info is not None:
            trade_modes.append({
                'symbol': symbol.name,
                'trade_mode': symbol_info.trade_mode
            })

    mt5.shutdown()

    return pd.DataFrame(trade_modes)

def print_trade_modes():
    df = get_trade_modes()
    if df is not None:
        # trade_mode에 대한 설명 딕셔너리
        mode_descriptions = {
            mt5.SYMBOL_TRADE_MODE_DISABLED: "거래 비활성화",
            mt5.SYMBOL_TRADE_MODE_LONGONLY: "롱 포지션만 허용",
            mt5.SYMBOL_TRADE_MODE_SHORTONLY: "숏 포지션만 허용",
            mt5.SYMBOL_TRADE_MODE_CLOSEONLY: "포지션 종료만 허용",
            mt5.SYMBOL_TRADE_MODE_FULL: "모든 거래 작업 허용"
        }

        # 결과 출력
        for _, row in df.iterrows():
            mode = row['trade_mode']
            description = mode_descriptions.get(mode, "알 수 없는 모드")
            print(f"심볼: {row['symbol']}, trade_mode: {mode} ({description})")

if __name__ == "__main__":
    print_trade_modes()
