class Logger:
    def __init__(self, log_path):
        print(f"Logger 초기화: {log_path}")
        
    def info(self, message):
        print(f"INFO: {message}")
        
    def error(self, message):
        print(f"ERROR: {message}") 