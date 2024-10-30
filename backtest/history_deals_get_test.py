import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def get_last_30days_deals():
    """현재 시간 기준으로 30일간의 거래 내역 가져오기"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # 현재 서버 시간 (UTC+2)
    tick = mt5.symbol_info_tick("BITCOIN")
    current_time = tick.time
    from_time = current_time - (30 * 24 * 60 * 60)  # 30일을 초 단위로 계산
    
    print("\n=== MT5 거래 내역 요청 정보 ===")
    print(f"시작 timestamp (UTC+2): {from_time}")
    print(f"종료 timestamp (UTC+2): {current_time}")

    # 거래 내역 요청 (이미 UTC+2 기준)
    deals = mt5.history_deals_get(from_time, current_time)

    if deals is None or len(deals) == 0:
        print("거래 내역이 없거나 요청 실패")
        return None

    # 거래 내역을 DataFrame으로 변환
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    
    # 시간 컬럼 변환
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print("\n=== 가져온 거래 내역 정보 ===")
    print(f"총 거래 수: {len(df)}")
    if len(df) > 0:
        print(f"첫 거래 시간: {df['time'].min()}")
        print(f"마지막 거래 시간: {df['time'].max()}")
        
        print("\n=== 거래 통계 ===")
        print(f"심볼별 거래 수:")
        print(df['symbol'].value_counts())
        
        print(f"\n거래 유형별 수:")
        print(df['type'].value_counts())
        
        print("\n=== 거래 내역 샘플 ===")
        print(df[['time', 'symbol', 'type', 'volume', 'price', 'profit']])

    return df

if __name__ == '__main__':
    # 테스트 실행
    df = get_last_30days_deals()
