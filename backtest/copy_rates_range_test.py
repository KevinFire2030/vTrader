import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def get_last_60_minutes_data(symbol):
    """현재 시간 기준 60개의 1분봉 데이터 가져오기"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # 현재 서버 시간 (UTC+2)
    tick = mt5.symbol_info_tick("BITCOIN")
    current_time = tick.time
    from_time = current_time - (60 * 60)  # 60분을 초 단위로 계산
    
    print("\n=== MT5 데이터 요청 정보 ===")
    print(f"심볼: {symbol}")
    print(f"시작 timestamp (UTC+2): {from_time}")
    print(f"종료 timestamp (UTC+2): {current_time}")

    # 데이터 요청 (UTC+2 기준)
    rates = mt5.copy_rates_range(
        symbol,
        mt5.TIMEFRAME_M1,
        datetime.fromtimestamp(from_time),
        datetime.fromtimestamp(current_time)
    )

    mt5.shutdown()

    if rates is None:
        print("데이터 요청 실패")
        return None

    # 데이터프레임 변환
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    print("\n=== 가져온 데이터 정보 ===")
    print(f"데이터 개수: {len(df)}")
    print(f"시작 시간: {df.index[0]}")
    print(f"종료 시간: {df.index[-1]}")
    
    # 데이터 출력
    print("\n=== 데이터 샘플 ===")
    print(df)

    return df

if __name__ == '__main__':
    # 테스트 실행
    symbol = "BITCOIN"
    df = get_last_60_minutes_data(symbol)
