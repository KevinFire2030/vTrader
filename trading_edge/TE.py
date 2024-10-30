import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def initialize_mt5():
    if not mt5.initialize():
        print(f"MetaTrader5 초기화 실패, 에러 코드 = {mt5.last_error()}")
        return False
    return True

def get_server_time():
    symbol = "EURUSD"  # 임의의 심볼 선택 (서버 시간을 가져오기 위함)
    symbol_info = mt5.symbol_info_tick(symbol)
    if symbol_info is None:
        print(f"{symbol} 심볼 정보를 가져오는데 실패했습니다.")
        return None
    return pd.to_datetime(symbol_info.time, unit='s')

def get_trade_history(days_ago=30):
    """
    MetaTrader5에서 지정된 기간 동안의 거래 내역을 가져옵니다.
    
    :param days_ago: 몇 일 전부터의 데이터를 가져올지 지정 (기본값: 30일)
    :return: 거래 내역이 담긴 DataFrame 또는 None (실패 시)
    """
    if not initialize_mt5():
        return None

    # 서버 시간 가져오기
    to_date = get_server_time()
    if to_date is None:
        print("서버 시간을 가져오는데 실패했습니다.")
        return None

    from_date = to_date - timedelta(days=days_ago)

    # 거래 내역 가져오기
    trades = mt5.history_deals_get(from_date, to_date)
    
    if trades is None or len(trades) == 0:
        print("거래 내역을 가져오는데 실패했거나 거래 내역이 없습니다.")
        mt5.shutdown()
        return None

    # 거래 내역의 구조 출력
    print("\n거래 내역 구조:")
    for key, value in trades[0]._asdict().items():
        print(f"{key}: {type(value)} - {value}")

    # 결과를 DataFrame으로 변환
    df = pd.DataFrame(list(trades), columns=trades[0]._asdict().keys())
    
    # 시간 데이터 변환
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['time_msc'] = pd.to_datetime(df['time_msc'], unit='ms')
    
    # 거래 유형 변환
    df['type'] = df['type'].map({0: 'buy', 1: 'sell', 2: 'buy', 3: 'sell', 4: 'buy', 5: 'sell'})
    
    # 컬럼 설명 추가
    column_descriptions = {
        'ticket': '거래 티켓 번호',
        'order': '주문 티켓 번호',
        'time': '거래 실행 시간',
        'time_msc': '거래 실행 시간 (밀리초)',
        'type': '거래 유형',
        'entry': '진입 유형',  # 이 부분을 확인해 주세요
        'magic': 'EA 매직 넘버',
        'position_id': '포지션 ID',
        'reason': '거래 실행 이유',
        'volume': '거래량',
        'price': '거래 가격',
        'commission': '수수료',
        'swap': '스왑',
        'profit': '손익',
        'fee': '추가 수수료',
        'symbol': '거래 심볼',
        'comment': '거래 코멘트',
        'external_id': '외부 시스템 ID'
    }
    
    df = df.rename(columns=column_descriptions)

    mt5.shutdown()
    return df

def get_closed_trades(df):
    """
    거래 내역에서 청산된 거래만 필터링합니다.
    
    :param df: 전체 거래 내역이 담긴 DataFrame
    :return: 청산된 거래만 담긴 DataFrame
    """
    return df[df['진입 유형'] == 1]  # 1은 청산을 의미합니다

def save_to_excel(df, filename):
    """
    DataFrame을 Excel 파일로 저장합니다.
    
    :param df: 저장할 DataFrame
    :param filename: 저장할 파일 이름
    """
    if df is None or df.empty:
        print("저장할 데이터가 없습니다.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "거래 내역"

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    try:
        wb.save(filename)
        print(f"결과가 {filename}에 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")

def analyze_closed_trades(filename):
    """
    청산 내역을 분석합니다.
    
    :param filename: 청산 내역이 저장된 Excel 파일 이름
    :return: 분석 결과 딕셔너리
    """
    # Excel 파일 읽기
    df = pd.read_excel(filename)
    
    # 총 포지션 청산 횟수
    total_closed = len(df)
    
    # 롱포지션과 숏포지션 청산 횟수
    long_closed = len(df[df['거래 유형'] == 'sell'])
    short_closed = len(df[df['거래 유형'] == 'buy'])
    
    # 수익 거래와 손실 거래 분리
    profitable_trades = df[df['손익'] > 0]
    losing_trades = df[df['손익'] <= 0]
    
    # 승률 계산
    win_rate = len(profitable_trades) / total_closed if total_closed > 0 else 0
    
    # 평균 수익과 평균 손실 계산
    avg_profit = profitable_trades['손익'].mean() if len(profitable_trades) > 0 else 0
    avg_loss = abs(losing_trades['손익'].mean()) if len(losing_trades) > 0 else 0
    
    # RR비율 계산
    rr_ratio = avg_profit / avg_loss if avg_loss != 0 else float('inf')
    
    # 기대값 TE 계산
    te = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
    
    # 결과 딕셔너리 생성
    results = {
        "총 포지션 청산 횟수": total_closed,
        "롱포지션 청산": long_closed,
        "숏포지션 청산": short_closed,
        "승률": win_rate,
        "평균 수익": avg_profit,
        "평균 손실": avg_loss,
        "RR비율": rr_ratio,
        "기대값 TE": te
    }
    
    return results

if __name__ == "__main__":
    trade_history = get_trade_history(days_ago=2)  # 30일간의 거래 내역 가져오기
    if trade_history is not None:
        print("\n거래 내역 샘플:")
        print(trade_history.head())
        print(f"\n총 {len(trade_history)}개의 거래를 가져왔습니다.")
        
        # 전체 거래 내역 저장
        all_trades_filename = "거래내역.xlsx"
        save_to_excel(trade_history, all_trades_filename)
        
        # 청산 내역만 필터링하여 저장
        closed_trades = get_closed_trades(trade_history)
        closed_trades_filename = "청산 내역.xlsx"
        save_to_excel(closed_trades, closed_trades_filename)
        print(f"\n총 {len(closed_trades)}개의 청산 거래를 저장했습니다.")
        
        # 청산 내역 분석
        analysis_results = analyze_closed_trades("청산 내역.xlsx")
        
        print("\n청산 내역 분석 결과:")
        for key, value in analysis_results.items():
            if key in ["총 포지션 청산 횟수", "롱포지션 청산", "숏포지션 청산"]:
                print(f"{key}: {value}회")
            elif key == "승률":
                print(f"{key}: {value:.2%}")
            elif key in ["평균 수익", "평균 손실", "기대값 TE"]:
                print(f"{key}: ${value:.2f}")
            elif key == "RR비율":
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
    else:
        print("거래 내역을 가져오는데 실패했습니다.")
