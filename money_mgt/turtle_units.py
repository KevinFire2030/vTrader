import sys
import os
import MetaTrader5 as mt5

# 현재 스크립트의 디렉토리를 파이썬 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from money_mgt.atr import calculate_atr
from money_mgt.symbol_info import print_symbol_info

def calculate_turtle_units(symbol, account_value, risk_percent, timeframe=mt5.TIMEFRAME_M1):
    """
    터틀 트레이딩 시스템의 유닛 수를 계산합니다.
    
    :param symbol: 심볼 이름 (예: "EURUSD")
    :param account_value: 계좌 가치
    :param risk_percent: 리스크 비율 (예: 0.01 for 1%)
    :param timeframe: 시간프레임 (기본값: 1분)
    :return: 유닛 수, ATR, 실제 리스크 비율
    """
    # ATR 계산
    atr, _ = calculate_atr(symbol, timeframe)
    print(f"{symbol}의 ATR: {atr:.5f}")
    
    if atr is None:
        print(f"ATR 계산 실패: {symbol}")
        return None, None, None

    # 심볼 정보 가져오기
    if not mt5.initialize():
        print(f"initialize() 실패, 에러 코드 = {mt5.last_error()}")
        return None, None, None

    symbol_info = mt5.symbol_info(symbol)
    mt5.shutdown()

    if symbol_info is None:
        print(f"심볼 정보 가져오기 실패: {symbol}")
        return None, None, None

    # 달러 변동폭 계산
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    dollar_volatility = (atr / tick_size) * tick_value

    # 유닛 크기 계산
    risk_amount = account_value * risk_percent
    unit_size = risk_amount / dollar_volatility

    # 최소 거래 단위로 반올림
    min_lot = symbol_info.volume_min
    units = max(min_lot, round(unit_size / min_lot) * min_lot)

    # 실제 리스크 계산
    actual_risk = (units * dollar_volatility) / account_value

    return units, atr, actual_risk

# 사용 예시
if __name__ == "__main__":
    symbol = "BITCOIN"
    account_value = 100 # 계좌 가치 $100
    risk_percent = 0.01  # 1% 리스크

    units, atr, actual_risk = calculate_turtle_units(symbol, account_value, risk_percent)
    if units is not None:
        print(f"{symbol}의 터틀 트레이딩 유닛 수: {units:.2f}")
        print(f"실제 리스크: {actual_risk:.2%}")

    # 심볼 정보 출력
    print("\n심볼 정보:")
    print_symbol_info(symbol)
