import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pytz
import pandas as pd

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    print("MT5 초기화 성공")
    return True

def get_account_info():
    account_info = mt5.account_info()
    if account_info:
        print(f"계정 번호: {account_info.login}")
        print(f"계정 서버: {account_info.server}")
        print(f"계정 통화: {account_info.currency}")
        print(f"레버리지: {account_info.leverage}")
        print(f"잔액: {account_info.balance}")
        print(f"이익: {account_info.profit}")
    else:
        print("계정 정보를 가져오는데 실패했습니다.")

def get_recent_trades(magic_number=123456):
    if not initialize_mt5():
        return None

    # MT5 서버 시간 확인
    server_time = datetime.fromtimestamp(mt5.symbol_info_tick("EURUSD").time)
    print(f"MT5 서버 시간: {server_time}")

    # 조회 시작 시간 설정 (7일 전)
    from_date = server_time - timedelta(days=7)
    to_date = server_time
    
    print(f"조회 시작 시간: {from_date}")
    print(f"조회 종료 시간: {to_date}")
    
    # 거래 내역 조회
    deals = mt5.history_deals_get(from_date, to_date)

    if deals is None or len(deals) == 0:
        print("해당 기간 동안의 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    # 매직 넘버로 필터링
    filtered_deals = [deal for deal in deals if deal.magic == magic_number]

    if len(filtered_deals) == 0:
        print(f"매직 넘버 {magic_number}에 해당하는 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    # DataFrame으로 변환
    df = pd.DataFrame(list(filtered_deals), columns=filtered_deals[0]._asdict().keys())
    
    # 시간 변환 (Unix timestamp to datetime)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 필요한 열만 선택
    df = df[['ticket', 'order', 'position_id', 'entry', 'price', 'volume']]
    
    # entry 열 변환
    df['entry'] = df['entry'].map({mt5.DEAL_ENTRY_IN: "In", mt5.DEAL_ENTRY_OUT: "Out", mt5.DEAL_ENTRY_INOUT: "InOut", mt5.DEAL_ENTRY_OUT_BY: "OutBy"})
    
    mt5.shutdown()
    return df

if __name__ == "__main__":
    get_account_info()
    trades = get_recent_trades()
    if trades is not None:
        print("\n매직 넘버 123456의 거래 내역:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(trades)
        print(f"\n총 거래 수: {len(trades)}")
    else:
        print("거래 내역을 가져오는데 실패했습니다.")
