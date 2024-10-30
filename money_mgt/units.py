def calculate_units(account_value, risk_percent, N, dollar_volatility):
    """
    터틀 트레이딩 시스템의 유닛 수를 계산합니다.
    
    :param account_value: 계좌 가치
    :param risk_percent: 리스크 비율 (예: 0.01 for 1%)
    :param N: 평균 실제 범위 (ATR)
    :param dollar_volatility: 달러 변동폭 당 계약 수
    :return: 유닛 수
    """
    risk_amount = account_value * risk_percent
    unit_size = risk_amount / (N * dollar_volatility)
    return unit_size

# 사용 예시
account_value = 100000  # 계좌 가치 $100,000
risk_percent = 0.01  # 1% 리스크
N = 2.5  # ATR 값
dollar_volatility = 50  # 1달러 변동 시 $50 변화

units = calculate_units(account_value, risk_percent, N, dollar_volatility)
print(f"계산된 유닛 수: {units:.2f}")

