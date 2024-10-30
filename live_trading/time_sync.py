import mt5
import time

class TimeSync:
    @staticmethod
    def wait_for_next_minute():
        while True:
            server_time = mt5.symbol_info_tick("EURUSD").time
            seconds = server_time % 60
            
            if seconds == 0:
                return
            
            wait_seconds = 60 - seconds
            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 1))  # 최대 1초씩 대기 