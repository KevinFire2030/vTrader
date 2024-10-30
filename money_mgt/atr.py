import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import pandas_ta as ta

def calculate_atr(symbol, timeframe=mt5.TIMEFRAME_M1, period=20):
    """
    지정된 심볼의 1분봉 ATR을 계산합니다.
    
    :param symbol: 심볼 이름 (예: "EURUSD")
    :param timeframe: 시간프레임 (기본값: 1분)
    :param period: ATR 계산 기간 (기본값: 20)
    :return: 직접 계산한 ATR 값, pandas_ta로 계산한 ATR 값
    """
    if not mt5.initialize():
        print(f"initialize() 실패, 에러 코드 = {mt5.last_error()}")
        return None, None

    # 데이터 가져오기
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period + 1)
    mt5.shutdown()

    if rates is None or len(rates) < period + 1:
        print(f"{symbol} 데이터를 가져오는데 실패했습니다.")
        return None, None

    # 데이터프레임으로 변환
    df = pd.DataFrame(rates)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')

    # 직접 ATR 계산
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = np.abs(df['high'] - df['close'].shift())
    df['low_close'] = np.abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr'] = df['tr'].ewm(span=period, adjust=False).mean()

    # pandas_ta를 사용한 ATR 계산 (EMA 모드 사용)
    df['atr_ta'] = ta.atr(df['high'], df['low'], df['close'], length=period, mamode='ema')

    # 최신 ATR 값 반환
    return df['atr'].iloc[-1], df['atr_ta'].iloc[-1]

# 사용 예시
if __name__ == "__main__":
    symbol = "EURUSD"
    atr, atr_ta = calculate_atr(symbol)
    if atr is not None and atr_ta is not None:
        print(f"{symbol}의 1분봉 ATR (20기간 EMA):")
        print(f"직접 계산: {atr:.5f}")
        print(f"pandas_ta: {atr_ta:.5f}")
        print(f"차이: {abs(atr - atr_ta):.5f}")






