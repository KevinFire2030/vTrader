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

def calculate_1unit_and_risk(symbol, atr, account_value=100, risk_percent=0.01):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return None, None, None

    # 달러 변동폭 계산
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    dollar_volatility = (atr / tick_size) * tick_value

    # 유닛 크기 계산
    risk_amount = account_value * risk_percent
    unit_size = risk_amount / dollar_volatility

    # 최소 거래 단위로 반올림
    min_lot = symbol_info.volume_min
    units = max(min_lot, round(unit_size / min_lot) * min_lot)

    # Risk 계산
    actual_risk_pct = (units * dollar_volatility) / account_value
    actual_risk_amt = units * dollar_volatility

    return units, actual_risk_pct, actual_risk_amt

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
                if atr is not None:
                    one_unit, risk_pct, risk_amt = calculate_1unit_and_risk(symbol.name, atr)
                    symbol_info_list.append({
                        'Symbol': symbol.name,
                        'digits': info.digits,
                        'point': info.point,
                        'trade_tick_value': info.trade_tick_value,
                        'trade_tick_size': info.trade_tick_size,
                        'trade_contract_size': info.trade_contract_size,
                        'volume_max': info.volume_max,
                        'volume_step': info.volume_step,
                        '1m_20_atr': atr,
                        '1unit': one_unit,
                        'risk_pct': f"{risk_pct*100:.2f}%",
                        'risk_amt': f"{risk_amt:.2f}$"
                    })

    mt5.shutdown()
    return pd.DataFrame(symbol_info_list)

def save_to_excel(df, filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
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
        save_to_excel(df, "symbol_unit.xlsx")
