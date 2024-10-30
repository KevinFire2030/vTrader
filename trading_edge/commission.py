import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pytz

def get_server_time():
    """
    MT5 서버 시간을 가져오는 함수
    """
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    symbol_info = mt5.symbol_info_tick("EURUSD")
    server_time = datetime.fromtimestamp(symbol_info.time)

    mt5.shutdown()
    return server_time

def get_last_eurusd_trade():
    """
    EURUSD의 마지막 거래 내역을 가져오는 함수
    
    Returns:
        dict: EURUSD의 마지막 거래 정보를 담은 딕셔너리, 없으면 None
    """
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # 최근 100개의 거래 내역 가져오기 (충분히 최근 거래를 포함하도록)
    deals = mt5.history_deals_get(datetime.now() - timedelta(days=30), datetime.now())

    if deals is None or len(deals) == 0:
        print("최근 30일 동안의 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    # EURUSD의 가장 최근 거래 찾기
    last_eurusd_deal = None
    for deal in reversed(deals):
        if deal.symbol == "EURUSD":
            last_eurusd_deal = deal
            break

    mt5.shutdown()

    if last_eurusd_deal is None:
        return None

    # 거래 시간을 서버 시간으로 변환
    deal_time = datetime.fromtimestamp(last_eurusd_deal.time)

    return {
        "ticket": last_eurusd_deal.ticket,
        "time": deal_time,
        "type": "Buy" if last_eurusd_deal.type == mt5.DEAL_TYPE_BUY else "Sell",
        "volume": last_eurusd_deal.volume,
        "price": last_eurusd_deal.price,
        "commission": last_eurusd_deal.commission,
        "swap": last_eurusd_deal.swap,
        "profit": last_eurusd_deal.profit,
        "comment": last_eurusd_deal.comment,
    }

def get_eurusd_info():
    """
    EURUSD의 심볼 정보를 가져오는 함수
    """
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    symbol_info = mt5.symbol_info("EURUSD")
    mt5.shutdown()

    if symbol_info is None:
        return None

    return {
        "spread": symbol_info.spread,
        "trade_contract_size": symbol_info.trade_contract_size,
        "trade_tick_value": symbol_info.trade_tick_value,
        "trade_tick_size": symbol_info.trade_tick_size,
    }

if __name__ == "__main__":
    server_time = get_server_time()
    if server_time:
        print(f"MT5 서버 시간: {server_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("서버 시간을 가져오는데 실패했습니다.")

    last_trade = get_last_eurusd_trade()
    if last_trade:
        print("\nEURUSD의 마지막 거래 내역:")
        print(f"거래 ID: {last_trade['ticket']}")
        print(f"시간: {last_trade['time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"타입: {last_trade['type']}")
        print(f"거래량: {last_trade['volume']}")
        print(f"가격: {last_trade['price']}")
        print(f"커미션: {last_trade['commission']}")
        print(f"스왑: {last_trade['swap']}")
        print(f"수익: {last_trade['profit']}")
        print(f"코멘트: {last_trade['comment']}")
        
        # 1 lot당 커미션 계산
        commission_per_lot = abs(last_trade['commission'] / last_trade['volume'])
        print(f"1 lot당 커미션: {commission_per_lot:.2f}")

    else:
        print("EURUSD의 최근 거래 내역이 없습니다.")

    eurusd_info = get_eurusd_info()
    if eurusd_info:
        print("\nEURUSD 심볼 정보:")
        print(f"스프레드: {eurusd_info['spread']} 포인트")
        print(f"계약 크기: {eurusd_info['trade_contract_size']}")
        print(f"틱 가치: {eurusd_info['trade_tick_value']}")
        print(f"틱 크기: {eurusd_info['trade_tick_size']}")
    else:
        print("EURUSD 심볼 정보를 가져오는데 실패했습니다.")
