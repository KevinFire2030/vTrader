import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def get_last_5min_ticks(symbol):
    """현재 시간 기준으로 과거 5분 동안의 틱 데이터 가져오기"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # 현재 서버 시간 (UTC+2)
    tick = mt5.symbol_info_tick(symbol)
    current_time = tick.time
    from_time = current_time - (5 * 60)  # 5분을 초 단위로 계산
    
    print("\n=== MT5 틱 데이터 요청 정보 ===")
    print(f"심볼: {symbol}")
    print(f"시작 timestamp (UTC+2): {from_time}")
    print(f"종료 timestamp (UTC+2): {current_time}")

    # 틱 데이터 요청 (이미 UTC+2 기준)
    ticks = mt5.copy_ticks_range(symbol, from_time, current_time, mt5.COPY_TICKS_ALL)

    if ticks is None or len(ticks) == 0:
        print("틱 데이터가 없거나 요청 실패")
        return None

    # 틱 데이터를 DataFrame으로 변환
    df = pd.DataFrame(ticks)
    
    # 중복 제거 전 데이터 수
    print(f"\n중복 제거 전 틱 수: {len(df)}")
    
    # 시간 컬럼 변환 (밀리초 포함)
    df['time'] = pd.to_datetime(df['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # 모든 컬럼에 대해 중복 체크하여 제거
    df = df.drop_duplicates(subset=df.columns.tolist())
    df.set_index('time', inplace=True)
    
    print(f"중복 제거 후 틱 수: {len(df)}")
    
    print("\n=== 가져온 틱 데이터 정보 ===")
    print(f"총 틱 수: {len(df)}")
    if len(df) > 0:
        print(f"첫 틱 시간: {df.index[0]}")
        print(f"마지막 틱 시간: {df.index[-1]}")
        
        print("\n=== 틱 데이터 통계 ===")
        print(f"최소 Bid: {df['bid'].min():.2f}")
        print(f"최대 Ask: {df['ask'].max():.2f}")
        print(f"평균 스프레드: {(df['ask'] - df['bid']).mean():.5f}")
        
        print("\n=== 틱 데이터 컬럼 ===")
        print(df.columns.tolist())
        
        print("\n=== 틱 데이터 샘플 ===")
        print(df)

    return df

if __name__ == '__main__':
    # 테스트 실행
    symbol = "BITCOIN"
    df = get_last_5min_ticks(symbol)
