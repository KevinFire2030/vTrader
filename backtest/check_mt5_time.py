import sys
import os
from datetime import datetime, timedelta, UTC
import pytz

# 현재 스크립트의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
mt5_backtrader_path = os.path.join(project_root, 'mt5_backtrader')
sys.path.insert(0, mt5_backtrader_path)

import MetaTrader5 as mt5

def print_all_times():
    """모든 관련 시간을 출력"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    # 1. UTC 현재 시간
    utc_now = datetime.now(UTC)
    utc_timestamp = int(utc_now.timestamp())

    # 2. MT5 틱 시간
    tick = mt5.symbol_info_tick("BITCOIN")
    tick_timestamp = tick.time

    # 3. 주요 도시 시간대
    london_tz = pytz.timezone('Europe/London')
    moscow_tz = pytz.timezone('Europe/Moscow')
    newyork_tz = pytz.timezone('America/New_York')
    seoul_tz = pytz.timezone('Asia/Seoul')
    server_tz = pytz.FixedOffset(2 * 60)  # UTC+2로 수정
    
    london_time = datetime.now(london_tz)
    moscow_time = datetime.now(moscow_tz)
    newyork_time = datetime.now(newyork_tz)
    seoul_time = datetime.now(seoul_tz)
    server_time = datetime.now(server_tz)

    print("\n=== 시간 비교 ===")
    print(f"\n1) UTC 시간:")
    print(f"   시간: {utc_now}")
    print(f"   timestamp: {utc_timestamp}")
    
    print(f"\n2) MT5 틱 시간:")
    print(f"   timestamp: {tick_timestamp}")
    print(f"   변환 시간: {datetime.fromtimestamp(tick_timestamp)}")
    
    print(f"\n3) 시차 분석:")
    print(f"   초 단위 차이: {tick_timestamp - utc_timestamp}")
    print(f"   시간 단위 차이: {(tick_timestamp - utc_timestamp) / 3600:.2f}")

    print(f"\n4) 주요 도시 시간:")
    print(f"   런던:    {london_time} (UTC{london_time.strftime('%z')})")
    print(f"   서버:    {server_time} (UTC+02:00)")
    print(f"   모스크바: {moscow_time} (UTC{moscow_time.strftime('%z')})")
    print(f"   뉴욕:    {newyork_time} (UTC{newyork_time.strftime('%z')})")
    print(f"   서울:    {seoul_time} (UTC{seoul_time.strftime('%z')})")

    mt5.shutdown()

if __name__ == '__main__':
    print_all_times()
