import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import time

def get_server_time():
    """서버 시간을 밀리초 단위로 반환"""
    tick = mt5.symbol_info_tick("EURUSD")
    if tick is None:
        return None
    return tick.time

def initialize_data(symbol):
    """초기 61개 봉 데이터 로드"""
    rates = mt5.copy_rates_from_pos(
        symbol, 
        mt5.TIMEFRAME_M1,
        0,  # 시작 위치
        61  # 가져올 데이터 개수 (61개 요청)
    )
    
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # 마지막 미완성 봉을 제외하고 저장
        completed_data = df[:-1]  # 60개의 완성된 봉
        
        print(f"\n초기 데이터 로드:")
        print(f"전체 봉 개수: {len(df)}")
        print(f"완성된 봉 개수: {len(completed_data)}")
        print(f"시작: {completed_data.index[0]}")
        print(f"종료: {completed_data.index[-1]}")
        
        return completed_data
    return None

def update_data(symbol, current_data):
    """최근 2개 봉 데이터로 업데이트"""
    new_rates = mt5.copy_rates_from_pos(
        symbol, 
        mt5.TIMEFRAME_M1,
        0,  # 시작 위치
        2   # 가져올 데이터 개수
    )
    
    if new_rates is not None and len(new_rates) >= 2:
        new_df = pd.DataFrame(new_rates)
        new_df['time'] = pd.to_datetime(new_df['time'], unit='s')
        new_df.set_index('time', inplace=True)
        
        # 완성된 봉만 선택 (마지막 미완성 봉 제외)
        completed_candle = new_df.iloc[0:1]
        
        # 기존 데이터에 새로운 완성 봉 추가
        updated_data = pd.concat([
            current_data,
            completed_candle
        ]).tail(60)  # 60개 봉 유지
        
        print(f"\n데이터 업데이트:")
        print(f"새로운 완성 봉: {completed_candle.index[0]}")
        print(f"현재 완성된 봉 개수: {len(updated_data)}")
        
        # 완성된 마지막 두 봉의 상세 정보 출력
        print("\n완성된 마지막 두 봉 정보:")
        print(f"[-2] [{updated_data.index[-2]}] 시가: {updated_data['open'][-2]:.5f}, "
              f"고가: {updated_data['high'][-2]:.5f}, 저가: {updated_data['low'][-2]:.5f}, "
              f"종가: {updated_data['close'][-2]:.5f}, 볼륨: {updated_data['tick_volume'][-2]}")
        print(f"[-1] [{updated_data.index[-1]}] 시가: {updated_data['open'][-1]:.5f}, "
              f"고가: {updated_data['high'][-1]:.5f}, 저가: {updated_data['low'][-1]:.5f}, "
              f"종가: {updated_data['close'][-1]:.5f}, 볼륨: {updated_data['tick_volume'][-1]}")
        
        return updated_data
    return current_data

def monitor_feed():
    """데이터 피드 모니터링"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    try:
        symbol = "EURUSD"
        data = initialize_data(symbol)
        if data is None:
            print("초기 데이터 로드 실패")
            return
            
        print("\n데이터 피드 모니터링 시작...")
        print("Ctrl+C로 종료할 수 있습니다.")
        
        last_second = -1
        while True:
            server_time = get_server_time()
            if server_time is None:
                continue
                
            current_second = int(server_time % 60)
            
            # 새로운 분이 시작될 때만 업데이트
            if current_second == 0 and current_second != last_second:
                print("\n=== 새로운 분이 시작되었습니다! ===")
                data = update_data(symbol, data)
                
            last_second = current_second
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n프로그램 종료")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    monitor_feed() 