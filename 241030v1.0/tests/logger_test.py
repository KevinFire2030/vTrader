import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import unittest
import tempfile
import shutil
from utils.logger import Logger

class LoggerTest(unittest.TestCase):
    def setUp(self):
        """각 테스트 메서드 실행 전에 실행"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.logger = Logger(self.test_dir, "test_logger")
        
    def tearDown(self):
        """각 테스트 메서드 실행 후에 실행"""
        # 로그 핸들러 정리
        self.logger.cleanup()
        # 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_log_creation(self):
        """로그 파일 생성 테스트"""
        # 로그 메시지 작성
        self.logger.info("테스트 메시지")
        
        # 로그 파일 존재 확인
        log_files = os.listdir(self.test_dir)
        self.assertEqual(len(log_files), 1)
        
        # 로그 파일 내용 확인
        log_file = os.path.join(self.test_dir, log_files[0])
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("테스트 메시지", content)
        
    def test_log_levels(self):
        """로그 레벨별 출력 테스트"""
        test_messages = {
            'debug': "디버그 메시지",
            'info': "정보 메시지",
            'warning': "경고 메시지",
            'error': "에러 메시지",
            'critical': "치명적 오류 메시지"
        }
        
        # 각 레벨별 로그 메시지 작성
        for level, message in test_messages.items():
            getattr(self.logger, level)(message)
        
        # 로그 파일 내용 확인
        log_files = os.listdir(self.test_dir)
        log_file = os.path.join(self.test_dir, log_files[0])
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 각 메시지가 로그 파일에 있는지 확인
        for message in test_messages.values():
            self.assertIn(message, content)
            
    def test_file_rotation(self):
        """로그 파일 로테이션 테스트"""
        # 1MB 이상의 로그 메시지 생성
        large_message = "X" * 1024  # 1KB
        for _ in range(1100):  # 약 1.1MB
            self.logger.info(large_message)
            
        # 로그 파일이 2개 이상 생성되었는지 확인
        log_files = os.listdir(self.test_dir)
        self.assertGreater(len(log_files), 1)

if __name__ == '__main__':
    unittest.main() 