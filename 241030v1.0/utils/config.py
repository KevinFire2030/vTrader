class Config:
    def __init__(self, config_path):
        print(f"Config 초기화: {config_path}")
        
    def get_symbols(self):
        print("get_symbols: 거래 심볼 목록 조회")
        return ["EURUSD"]
        
    def get_log_path(self):
        print("get_log_path: 로그 경로 조회")
        return "./logs" 