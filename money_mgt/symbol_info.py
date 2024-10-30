import MetaTrader5 as mt5

def print_symbol_info(symbol):
    """
    지정된 금융 상품(심볼)에 대한 정보를 출력합니다.
    
    :param symbol: 금융 상품 이름 (예: "EURUSD")
    """
    if not mt5.initialize():
        print(f"initialize() 실패, 에러 코드 = {mt5.last_error()}")
        return

    # 심볼 정보 가져오기
    symbol_info = mt5.symbol_info(symbol)
    
    if symbol_info is None:
        print(f"{symbol} 심볼 정보를 가져오는데 실패했습니다.")
        mt5.shutdown()
        return

    print(f"{symbol} 심볼 정보:")
    print(f"스프레드: {symbol_info.spread}")
    print(f"소수점 자릿수: {symbol_info.digits}")
    print(f"계약 크기: {symbol_info.trade_contract_size}")
    print(f"최소 거래량: {symbol_info.volume_min}")
    print(f"최대 거래량: {symbol_info.volume_max}")
    print(f"거래량 단계: {symbol_info.volume_step}")
    print(f"포인트: {symbol_info.point}")
    print(f"틱 가치: {symbol_info.trade_tick_value}")
    print(f"틱 크기: {symbol_info.trade_tick_size}")
    print(f"통화 기준: {symbol_info.currency_base}")
    print(f"수익 통화: {symbol_info.currency_profit}")
    print(f"설명: {symbol_info.description}")

    mt5.shutdown()

# 사용 예시
if __name__ == "__main__":
    print_symbol_info("EURUSD")

