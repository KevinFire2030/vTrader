import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from live_feed import LiveFeed

def test_mt5_connection():
    """MT5 연결 테스트"""
    print("\n=== MT5 연결 테스트 ===")
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    
    account_info = mt5.account_info()
    if account_info is None:
        print("계좌 정보 조회 실패")
        return False
        
    print(f"계좌 번호: {account_info.login}")
    print(f"계좌 잔고: {account_info.balance}")
    print(f"계좌 자산: {account_info.equity}")
    return True

def test_symbol_data(symbol="EURUSD"):
    """심볼 데이터 테스트"""
    print(f"\n=== {symbol} 데이터 테스트 ===")
    
    # 심볼 정보 확인
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} 심볼 정보 없음")
        return False
        
    print(f"심볼: {symbol_info.name}")
    print(f"최소 거래량: {symbol_info.volume_min}")
    print(f"틱 크기: {symbol_info.point}")
    
    # 가격 데이터 확인
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    if rates is None:
        print("가격 데이터 조회 실패")
        return False
        
    df = pd.DataFrame(rates)
    print("\n가격 데이터 샘플:")
    print(df.tail())
    return df

def test_indicators(df):
    """지표 계산 테스트"""
    print("\n=== 지표 계산 테스트 ===")
    
    try:
        # EMA 계산
        df['ema5'] = ta.ema(df['close'], length=5)
        df['ema20'] = ta.ema(df['close'], length=20)
        df['ema40'] = ta.ema(df['close'], length=40)
        
        # ATR 계산
        df['atr'] = ta.atr(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            length=20,
            mamode='ema'
        )
        
        print("\n지표 계산 결과:")
        print(df[['close', 'ema5', 'ema20', 'ema40', 'atr']].tail())
        return True
        
    except Exception as e:
        print(f"지표 계산 실패: {str(e)}")
        return False

def test_live_feed(symbol="EURUSD"):
    """LiveFeed 클래스 테스트"""
    print("\n=== LiveFeed 테스트 ===")
    
    try:
        feed = LiveFeed([symbol])
        df = feed.get_data(symbol)
        
        if df is not None:
            print("\nLiveFeed 데이터:")
            print(df.tail())
            return True
        else:
            print("LiveFeed 데이터 없음")
            return False
            
    except Exception as e:
        print(f"LiveFeed 테스트 실패: {str(e)}")
        return False

def main():
    """테스트 실행"""
    try:
        # MT5 연결 테스트
        if not test_mt5_connection():
            return
        
        # 심볼 데이터 테스트
        df = test_symbol_data()
        if df is None:
            return
            
        # 지표 계산 테스트
        if not test_indicators(df):
            return
            
        # LiveFeed 테스트
        if not test_live_feed():
            return
            
        print("\n모든 테스트 완료")
        
    except Exception as e:
        print(f"\n테스트 중 오류 발생: {str(e)}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main() 