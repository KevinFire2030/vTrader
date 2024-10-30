import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import pytz
import os

def get_server_time():
    """MT5 서버 시간을 가져오는 함수"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None
    
    server_time = mt5.symbol_info_tick("EURUSD").time
    mt5.shutdown()
    return datetime.fromtimestamp(server_time, tz=pytz.timezone('Europe/Moscow'))

def get_trade_history(magic_number, days=30):
    """
    지정된 매직 넘버의 거래 내역을 DataFrame으로 반환하는 함수

    Args:
        magic_number (int): 조회할 거래의 매직 넘버
        days (int): 조회할 기간 (일 단위, 기본값 30일)

    Returns:
        pd.DataFrame: 거래 내역을 담은 DataFrame
    """
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    utc_tz = pytz.UTC
    from_date = datetime.now(utc_tz) - timedelta(days=days)
    to_date = datetime.now(utc_tz)
    
    print(f"조회 시작 시간 (UTC): {from_date}")
    print(f"조회 종료 시간 (UTC): {to_date}")
    
    deals = mt5.history_deals_get(from_date, to_date)

    if deals is None or len(deals) == 0:
        print(f"해당 기간 동안의 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    # 매직 넘버로 필터링
    deals = [deal for deal in deals if deal.magic == magic_number]

    if len(deals) == 0:
        print(f"매직 넘버 {magic_number}에 해당하는 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['time_msc'] = pd.to_datetime(df['time_msc'], unit='ms', utc=True)
    
    # 필요하다면 여기서 모스크바 시간으로 변환
    moscow_tz = pytz.timezone('Europe/Moscow')
    df['time_moscow'] = df['time'].dt.tz_convert(moscow_tz)
    df['time_msc_moscow'] = df['time_msc'].dt.tz_convert(moscow_tz)
    
    # 거래 유형을 문자열로 변환
    df['type'] = df['type'].map({mt5.DEAL_TYPE_BUY: "Buy", mt5.DEAL_TYPE_SELL: "Sell"})
    
    # 진입 유형을 문자열로 변환
    df['entry'] = df['entry'].map({mt5.DEAL_ENTRY_IN: "In", mt5.DEAL_ENTRY_OUT: "Out", mt5.DEAL_ENTRY_INOUT: "InOut", mt5.DEAL_ENTRY_OUT_BY: "OutBy"})
    
    mt5.shutdown()
    return df

def print_trade_statistics(df):
    """
    거래 통계를 출력하는 함수

    Args:
        df (pd.DataFrame): 거래 내역 DataFrame
    """
    print("\n거래 통계:")
    print(f"총 거래 횟수: {len(df)}")
    print(f"총 수익: {df['profit'].sum():.2f}")
    print(f"총 수수료: {df['commission'].sum():.2f}")
    print(f"총 스왑: {df['swap'].sum():.2f}")
    print(f"순 수익: {(df['profit'].sum() - df['commission'].sum() - df['swap'].sum()):.2f}")

def save_to_excel(df, magic_number):
    """
    DataFrame을 엑셀 파일로 저장하는 함수

    Args:
        df (pd.DataFrame): 저장할 DataFrame
        magic_number (int): 매직 넘버
    """
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trade_history_magic_{magic_number}_{current_time}.xlsx"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    # 시간 열을 문자열로 변환
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['time_msc'] = df['time_msc'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # DataFrame을 엑셀 파일로 저장
    df.to_excel(file_path, index=False, engine='openpyxl')
    print(f"거래 내역이 {file_path} 파일로 저장되었습니다.")

if __name__ == "__main__":
    try:
        magic_number = int(input("조회할 거래의 매직 넘버를 입력하세요: "))
        days = int(input("조회할 기간을 입력하세요 (일 단위): "))
        
        print(f"\n현재 시간 (로컬): {datetime.now()}")
        print(f"현재 시간 (UTC): {datetime.now(pytz.UTC)}")
        print(f"현재 시간 (모스크바): {datetime.now(pytz.timezone('Europe/Moscow'))}")
        
        df = get_trade_history(magic_number, days)
        if df is not None:
            print(f"\n매직 넘버 {magic_number}의 최근 {days}일 거래 내역:")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print(df)
            
            print_trade_statistics(df)
            
            # 엑셀 파일로 저장
            save_to_excel(df, magic_number)
    except ValueError:
        print("올바른 숫자를 입력해주세요.")
