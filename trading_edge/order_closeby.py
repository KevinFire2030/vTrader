import MetaTrader5 as mt5
import time

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    return True

def open_position(symbol, lot, order_type):
    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result

def close_by_positions(symbol, ticket1, ticket2):
    request = {
        "action": mt5.TRADE_ACTION_CLOSE_BY,
        "symbol": symbol,
        "position": ticket1,
        "position_by": ticket2,
        "magic": 234000,
        "comment": "python script close by",
    }
    
    result = mt5.order_send(request)
    return result

def demonstrate_close_by(symbol, lot):
    if not initialize_mt5():
        return

    print(f"데모 시작: {symbol}, 거래량: {lot}")

    # 매수 포지션 오픈
    buy_result = open_position(symbol, lot, mt5.ORDER_TYPE_BUY)
    if buy_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("매수 주문 실패")
        return
    print(f"매수 포지션 오픈: 티켓 {buy_result.order}")

    # 매도 포지션 오픈 (헤지)
    sell_result = open_position(symbol, lot, mt5.ORDER_TYPE_SELL)
    if sell_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("매도 주문 실패")
        return
    print(f"매도 포지션 오픈 (헤지): 티켓 {sell_result.order}")

    # 잠시 대기
    time.sleep(5)

    # CLOSE BY 주문 실행
    close_result = close_by_positions(symbol, buy_result.order, sell_result.order)
    if close_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("CLOSE BY 주문 실패")
    else:
        print(f"CLOSE BY 주문 성공: 티켓 {close_result.order}")

    # 최종 포지션 확인
    positions = mt5.positions_get(symbol=symbol)
    print(f"남은 포지션 수: {len(positions)}")
    for position in positions:
        print(f"포지션: 티켓 {position.ticket}, 타입 {'매수' if position.type == 0 else '매도'}, 수량 {position.volume}")

    mt5.shutdown()

if __name__ == "__main__":
    symbol = "EURUSD"
    lot = 0.1
    demonstrate_close_by(symbol, lot)
