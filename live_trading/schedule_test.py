import schedule
import time
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def get_server_time():
    """MT5 서버 시간 조회"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None
    
    # 서버 시간 정보 조회
    server_time = None
    try:
        # 여러 활성 심볼을 순회하며 최신 시간 확인
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "#USNDAQ100"]
        for symbol in symbols:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                if server_time is None or tick.time > server_time:
                    server_time = tick.time
    except Exception as e:
        print(f"서버 시간 조회 실패: {e}")
        return None
    
    return datetime.utcfromtimestamp(server_time)

def format_time_and_delays(local_time, server_time):
    """시간 포맷팅 및 지연 시간 계산"""
    # UTC+2 시간 계산 (로컬 시간에서 7시간 차감)
    utc2_time = local_time - timedelta(hours=7)
    
    # 지연 시간 계산
    local_delay = (server_time + timedelta(hours=7) - local_time).total_seconds()
    utc2_delay = (server_time - utc2_time).total_seconds()
    
    return (
        f"[Local: {local_time.strftime('%H:%M:%S.%f')[:-4]}] "
        f"[UTC+2: {utc2_time.strftime('%H:%M:%S')}] "
        f"[Server: {server_time.strftime('%H:%M:%S')}] "
        f"(지연: 로컬 {local_delay:.3f}초, UTC+2 {utc2_delay:.3f}초)"
    )

def get_last_two_bars(symbol):
    """최근 2개 분봉 데이터 조회"""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 2)
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    return None

def data_feed_job():
    """매분 정시에 실행되는 작업"""
    local_time = datetime.now()
    server_time = get_server_time()
    if server_time:
        print(f"{format_time_and_delays(local_time, server_time)} data_feed")
        
        # 최근 2개 분봉 데이터 출력
        symbols = ["#USNDAQ100"]
        for symbol in symbols:
            df = get_last_two_bars(symbol)
            if df is not None:
                print(f"\n{symbol}[-2] [{df.iloc[0]['time']}] "
                      f"시가: {df.iloc[0]['open']:.2f}, "
                      f"고가: {df.iloc[0]['high']:.2f}, "
                      f"저가: {df.iloc[0]['low']:.2f}, "
                      f"종가: {df.iloc[0]['close']:.2f}, "
                      f"거래량: {df.iloc[0]['real_volume']:.0f}")
                print(f"{symbol}[-1] [{df.iloc[1]['time']}] "
                      f"시가: {df.iloc[1]['open']:.2f}, "
                      f"고가: {df.iloc[1]['high']:.2f}, "
                      f"저가: {df.iloc[1]['low']:.2f}, "
                      f"종가: {df.iloc[1]['close']:.2f}, "
                      f"거래량: {df.iloc[1]['real_volume']:.0f}")

def trading_job():
    """10초마다 실행되는 작업"""
    # 출력 없이 실행
    server_time = get_server_time()

def main():
    """메인 함수"""
    print("프로그램 시작")
    
    # MT5 서버 시간 조회
    local_time = datetime.now()
    server_time = get_server_time()
    if not server_time:
        print("서버 시간 조회 실패")
        return
        
    print(f"시작 시간: {format_time_and_delays(local_time, server_time)}")
    
    try:
        # 매분 0초에 data_feed_job 실행
        schedule.every().minute.at(":03").do(data_feed_job)
        
        # 10초마다 trading_job 실행
        schedule.every(10).seconds.do(trading_job)
        
        # 스케줄 실행
        while True:
            schedule.run_pending()
            time.sleep(0.1)  # CPU 부하 감소
            
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    finally:
        mt5.shutdown()

if __name__ == '__main__':
    main() 