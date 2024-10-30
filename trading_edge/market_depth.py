import MetaTrader5 as mt5
import pandas as pd

def print_market_depth(symbol):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    # 심볼 선택
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} 심볼을 선택할 수 없습니다.")
        mt5.shutdown()
        return

    # Market Depth 구독
    if not mt5.market_book_add(symbol):
        print(f"{symbol}에 대한 Market Depth를 구독할 수 없습니다.")
        mt5.shutdown()
        return

    # Market Depth 정보 가져오기
    depth = mt5.market_book_get(symbol)
    if depth is None:
        print(f"{symbol}에 대한 Market Depth 정보를 가져올 수 없습니다.")
        mt5.market_book_release(symbol)
        mt5.shutdown()
        return

    # 데이터 정리
    bids = [d for d in depth if d.type == mt5.BOOK_TYPE_SELL]
    asks = [d for d in depth if d.type == mt5.BOOK_TYPE_BUY]

    # DataFrame 생성
    df_bids = pd.DataFrame([{'Price': b.price, 'Volume': b.volume, 'Volume_dbl': b.volume_dbl} for b in bids])
    df_asks = pd.DataFrame([{'Price': a.price, 'Volume': a.volume, 'Volume_dbl': a.volume_dbl} for a in asks])

    # 결과 출력
    print(f"{symbol} Market Depth:")
    print("\nBids (매수 주문):")
    print(df_bids.to_string(index=False))
    print("\nAsks (매도 주문):")
    print(df_asks.to_string(index=False))

    # Market Depth 구독 해제
    mt5.market_book_release(symbol)
    mt5.shutdown()

if __name__ == "__main__":
    symbol = input("심볼을 입력하세요: ")
    print_market_depth(symbol)
