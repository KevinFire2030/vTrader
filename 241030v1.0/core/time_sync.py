import MetaTrader5 as mt5
import time
import statistics
from datetime import datetime

class TimeSync:
    """시간 동기화 관리"""
    def __init__(self):
        # MT5 초기화는 외부에서 이미 완료되었다고 가정
        self.server_offset = None  # 서버-로컬 시간 차이
        self.reference_symbol = "#USNDAQ100"  # 기준 심볼 변경
        self.sync_samples = 10     # 동기화 샘플 수
        self.sync_interval = 0.1   # 샘플링 간격
        self.max_latency = 1.0     # 최대 허용 지연시간
        
        # 심볼 존재 확인
        symbols = mt5.symbols_get()
        if symbols is None:
            raise Exception("심볼 정보 조회 실패")
            
        available_symbols = [s.name for s in symbols]
        if self.reference_symbol not in available_symbols:
            raise Exception(f"{self.reference_symbol} 심볼을 찾을 수 없음")
        
        # 초기 동기화
        self.server_offset = self.calculate_offset()
        
    def get_server_time(self):
        """서버 시간 조회"""
        # 연결 상태 확인
        if not mt5.initialize():
            print("MT5 연결 실패")
            return None
            
        tick = mt5.symbol_info_tick(self.reference_symbol)
        if tick is None:
            print(f"{self.reference_symbol} 틱 정보 조회 실패")
            return None
            
        return float(tick.time)  # float로 변환
        
    def calculate_offset(self):
        """서버와 로컬 시간의 차이 계산"""
        samples = []
        
        for _ in range(self.sync_samples):
            start_local = time.time()
            server_time = self.get_server_time()
            end_local = time.time()
            
            if server_time is None:
                continue
                
            # 왕복 지연시간의 절반을 보정값으로 사용
            latency = (end_local - start_local) / 2
            if latency > self.max_latency:
                continue
                
            # 초 단위의 차이만 계산 (60초 이내)
            offset = (server_time - (start_local + latency)) % 60
            
            # 30초 이상 차이나면 반대 방향으로 계산
            if offset > 30:
                offset -= 60
                
            samples.append(offset)
            time.sleep(self.sync_interval)
        
        if not samples:
            return 0.0  # float로 반환
            
        # 이상치를 제거하고 중간값 계산
        samples.sort()
        return float(statistics.median(samples[1:-1] if len(samples) > 4 else samples))
        
    def wait_for_next_minute(self):
        """다음 분의 정각(00초)까지 대기"""
        while True:
            server_time = self.get_server_time()
            if server_time is None:
                time.sleep(0.1)
                continue
                
            seconds = float(server_time % 60)  # float로 변환
            if seconds == 0:
                return
                
            # 1초씩 대기 (긴 대기 시간 방지)
            wait_seconds = 60 - seconds
            time.sleep(min(1, wait_seconds))
            
    def check_sync_status(self):
        """시간 동기화 상태 확인"""
        server_time = self.get_server_time()
        if server_time is None:
            return False
            
        local_time = time.time()
        diff = abs(server_time - local_time) % 60
        
        # 1초 이상 차이나면 경고
        return diff < 1
        
    def handle_sync_error(self):
        """동기화 오류 처리"""
        retry_count = 3
        while retry_count > 0:
            if self.check_sync_status():
                return True
            # 재동기화 시도
            self.server_offset = self.calculate_offset()
            time.sleep(1)
            retry_count -= 1
        return False