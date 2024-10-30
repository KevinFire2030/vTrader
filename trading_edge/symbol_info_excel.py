import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import os

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    return True

def calculate_atr(symbol, timeframe=mt5.TIMEFRAME_M1, period=20):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('datetime', inplace=True)
    atr = ta.atr(df['high'], df['low'], df['close'], length=period, mamode='ema')
    return atr.iloc[-1]

def get_symbol_info():
    if not initialize_mt5():
        return None

    symbols = mt5.symbols_get()
    symbol_info_list = []

    for symbol in symbols:
        if symbol.visible:  # Market Watch에 있는 심볼만 선택
            info = mt5.symbol_info(symbol.name)
            if info is not None:
                atr = calculate_atr(symbol.name)
                symbol_info_list.append({
                    'Symbol': symbol.name,
                    'digits': info.digits,
                    'point': info.point,
                    'trade_tick_value': info.trade_tick_value,
                    'trade_tick_size': info.trade_tick_size,
                    'trade_contract_size': info.trade_contract_size,
                    'volume_max': info.volume_max,
                    'volume_step': info.volume_step,
                    '1m_20_atr': atr  # 여기서 컬럼명을 변경했습니다
                })

    mt5.shutdown()
    return pd.DataFrame(symbol_info_list)

def save_to_excel(df, filename):
    # 현재 스크립트의 디렉토리 경로를 가져옵니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 파일 경로를 생성합니다.
    file_path = os.path.join(current_dir, filename)
    
    try:
        df.to_excel(file_path, index=False)
        print(f"데이터가 {file_path}에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    df = get_symbol_info()
    if df is not None:
        print(df)  # 콘솔에 출력
        save_to_excel(df, "symbol_info.xlsx")
