import MetaTrader5 as mt5
import pandas as pd

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    return True

def get_option_symbols():
    if not initialize_mt5():
        return None

    all_symbols = mt5.symbols_get()
    option_symbols = []

    for symbol in all_symbols:
        symbol_info = mt5.symbol_info(symbol.name)
        if symbol_info is not None and symbol_info.option_mode != 0:
            option_symbols.append({
                'name': symbol.name,
                'option_mode': symbol_info.option_mode,
                'option_right': symbol_info.option_right,
                'option_strike': symbol_info.option_strike,
                'expiration_time': symbol_info.expiration_time
            })

    mt5.shutdown()
    return option_symbols

def print_option_symbols():
    option_symbols = get_option_symbols()
    if option_symbols is None:
        return

    if len(option_symbols) == 0:
        print("옵션 상품이 없습니다.")
        return

    df = pd.DataFrame(option_symbols)
    
    # option_mode와 option_right에 대한 설명 추가
    df['option_mode_desc'] = df['option_mode'].map({
        1: "유러피언",
        2: "아메리칸"
    })
    df['option_right_desc'] = df['option_right'].map({
        1: "콜",
        2: "풋"
    })

    # expiration_time을 읽기 쉬운 형식으로 변환
    df['expiration_time'] = pd.to_datetime(df['expiration_time'], unit='s')

    print("옵션 상품 목록:")
    for _, row in df.iterrows():
        print(f"심볼: {row['name']}")
        print(f"  옵션 유형: {row['option_mode_desc']} ({row['option_mode']})")
        print(f"  옵션 권리: {row['option_right_desc']} ({row['option_right']})")
        print(f"  행사 가격: {row['option_strike']}")
        print(f"  만기일: {row['expiration_time']}")
        print("---")

if __name__ == "__main__":
    print_option_symbols()
