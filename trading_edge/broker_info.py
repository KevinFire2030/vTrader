import MetaTrader5 as mt5

def print_broker_info():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return

    # 브로커 정보 가져오기
    account_info = mt5.account_info()
    if account_info is None:
        print("계정 정보를 가져올 수 없습니다.")
        mt5.shutdown()
        return

    # 브로커 정보 출력
    print("브로커 정보:")
    print(f"브로커: {account_info.company}")
    print(f"서버: {account_info.server}")
    print(f"계정 번호: {account_info.login}")
    print(f"계정 유형: {account_info.trade_mode}")
    print(f"레버리지: 1:{account_info.leverage}")
    print(f"잔고: {account_info.balance} {account_info.currency}")
    print(f"신용: {account_info.credit} {account_info.currency}")
    print(f"순자산: {account_info.equity} {account_info.currency}")
    print(f"마진: {account_info.margin} {account_info.currency}")
    print(f"가용 마진: {account_info.margin_free} {account_info.currency}")
    print(f"마진 레벨: {account_info.margin_level}%")

    mt5.shutdown()

if __name__ == "__main__":
    print_broker_info()
