import sys
import os

# 현재 Python의 모듈 검색 경로 출력
print("\nPython 모듈 검색 경로:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# 현재 스크립트의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (backtest 폴더의 상위 디렉토리)
project_root = os.path.dirname(current_dir)
# mt5_backtrader 폴더 경로
mt5_backtrader_path = os.path.join(project_root, 'mt5_backtrader')

print(f"\nmt5_backtrader 경로: {mt5_backtrader_path}")

# 시스템 경로에 mt5_backtrader 폴더를 추가
sys.path.insert(0, mt5_backtrader_path)

print("\n경로 추가 후 Python 모듈 검색 경로:")
for i, path in enumerate(sys.path):
    print(f"{i}: {path}")

# mt5_backtrader에서 backtrader를 import
import backtrader as bt

# backtrader의 위치 출력
print(f"\nUsing Backtrader from: {bt.__file__}")
