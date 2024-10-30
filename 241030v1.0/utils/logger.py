import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """로깅 시스템"""
    def __init__(self, log_path: str, name: str = "vTrader"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 로그 디렉토리 생성
        os.makedirs(log_path, exist_ok=True)
        
        # 로그 파일명 설정 (날짜별)
        today = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_path, f"{name}_{today}.log")
        
        # 파일 핸들러 설정 (1MB 크기 제한, 최대 30개 파일)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024*1024,  # 1MB
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 로그 포맷 설정
        log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 핸들러 저장 (cleanup을 위해)
        self.handlers = [file_handler, console_handler]
        
    def cleanup(self):
        """로그 핸들러 정리"""
        for handler in self.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        
    def debug(self, message: str):
        """디버그 로그"""
        self.logger.debug(message)
        
    def info(self, message: str):
        """정보 로그"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """경고 로그"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """에러 로그"""
        self.logger.error(message)
        
    def critical(self, message: str):
        """치명적 오류 로그"""
        self.logger.critical(message) 