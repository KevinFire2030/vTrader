import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    return True

def open_position(symbol, lot, order_type):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"심볼 {symbol}에 대한 정보를 가져올 수 없습니다.")
        return None

    point = symbol_info.point
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    deviation = symbol_info.trade_stops_level

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script open",
        "type_time": symbol_info.expiration_mode,
        "type_filling": symbol_info.filling_mode,
    }
    result = mt5.order_send(request)
    return result

def close_position(position):
    symbol_info = mt5.symbol_info(position.symbol)
    if symbol_info is None:
        print(f"심볼 {position.symbol}에 대한 정보를 가져올 수 없습니다.")
        return None

    tick = mt5.symbol_info_tick(position.symbol)
    deviation = symbol_info.trade_stops_level

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
        "position": position.ticket,
        "price": tick.bid if position.type == 0 else tick.ask,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script close",
        "type_time": symbol_info.expiration_mode,
        "type_filling": symbol_info.filling_mode,
    }
    result = mt5.order_send(request)
    return result

def simulate_hedge_and_close(symbol, lot):
    if not initialize_mt5():
        return

    print(f"시뮬레이션 시작: {symbol}, 거래량: {lot}")

    # 시나리오 1: 헤지
    print("\n시나리오 1: 헤지")
    buy_result = open_position(symbol, lot, mt5.ORDER_TYPE_BUY)
    if buy_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("매수 주문 실패")
        return
    print(f"매수 포지션 오픈: 티켓 {buy_result.order}")

    sell_result = open_position(symbol, lot, mt5.ORDER_TYPE_SELL)
    if sell_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("매도 주문 실패")
        return
    print(f"매도 포지션 오픈 (헤지): 티켓 {sell_result.order}")

    positions = mt5.positions_get(symbol=symbol)
    print(f"열린 포지션 수: {len(positions)}")
    for position in positions:
        print(f"포지션: 티켓 {position.ticket}, 타입 {'매수' if position.type == 0 else '매도'}, 수량 {position.volume}")

    # 시나리오 2: 포지션 클로즈
    print("\n시나리오 2: 포지션 클로즈")
    buy_result = open_position(symbol, lot, mt5.ORDER_TYPE_BUY)
    if buy_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("매수 주문 실패")
        return
    print(f"매수 포지션 오픈: 티켓 {buy_result.order}")

    positions = mt5.positions_get(symbol=symbol)
    if positions:
        close_result = close_position(positions[0])
        if close_result.retcode != mt5.TRADE_RETCODE_DONE:
            print("포지션 클로즈 실패")
        else:
            print(f"포지션 클로즈: 티켓 {close_result.order}")
    
    positions = mt5.positions_get(symbol=symbol)
    print(f"열린 포지션 수: {len(positions)}")
    for position in positions:
        print(f"포지션: 티켓 {position.ticket}, 타입 {'매수' if position.type == 0 else '매도'}, 수량 {position.volume}")

    mt5.shutdown()

if __name__ == "__main__":
    symbol = "EURUSD"
    lot = 0.1
    simulate_hedge_and_close(symbol, lot)
