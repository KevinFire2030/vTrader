import MetaTrader5 as mt5
import time
from datetime import datetime
import statistics

def get_server_time():
    """서버 시간을 밀리초 단위로 반환"""
    tick = mt5.symbol_info_tick("EURUSD")
    if tick is None:
        return None
    return tick.time

def calculate_server_offset():
    """서버와 로컬 시간의 차이 계산"""
    samples = []
    print("서버 시간 오프셋 계산 중...")
    
    for i in range(10):
        start_local = time.time()
        server_time = get_server_time()
        end_local = time.time()
        
        if server_time is None:
            continue
            
        # 왕복 지연시간의 절반을 보정값으로 사용
        latency = (end_local - start_local) / 2
        offset = server_time - (start_local + latency)
        samples.append(offset)
        
        print(f"샘플 {i+1}: 오프셋 = {offset:.3f}초")
        time.sleep(0.1)
    
    # 이상치를 제거하고 중간값 계산
    samples.sort()
    median_offset = statistics.median(samples[2:-2])
    print(f"\n계산된 서버 시간 오프셋: {median_offset:.3f}초")
    return median_offset

def monitor_server_time():
    """서버 시간을 모니터링하고 00초일 때 기록"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    try:
        # 서버 시간 오프셋 계산
        server_offset = calculate_server_offset()
        print("\n서버 시간 모니터링 시작...")
        print("Ctrl+C로 종료할 수 있습니다.")
        
        last_second = -1
        while True:
            server_time = get_server_time()
            if server_time is None:
                continue
                
            # 현재 초 계산
            current_second = int(server_time % 60)
            
            # 새로운 초가 시작될 때만 출력
            if current_second != last_second:
                server_datetime = datetime.utcfromtimestamp(server_time)
                local_time = time.time()
                local_datetime = datetime.utcfromtimestamp(local_time)
                
                # 시차를 제외한 순수 초 단위 차이 계산
                time_diff = (local_time - server_time) % 60
                
                print(f"\n현재 서버 시간(UTC): {server_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                print(f"현재 로컬 시간(UTC): {local_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                print(f"시간 차이: {time_diff:.3f}초")
                
                # 00초일 때 특별히 표시
                if current_second == 0:
                    print("\n=== 새로운 분이 시작되었습니다! ===")
                
                last_second = current_second
            
            # CPU 사용량을 위해 아주 작은 대기 시간 추가
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n프로그램 종료")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    monitor_server_time() 