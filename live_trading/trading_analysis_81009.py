import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import pytz
import os
from openpyxl import load_workbook

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return False
    print("MT5 초기화 성공")
    return True

def get_recent_trades(magic_number=81009, days=7):
    if not initialize_mt5():
        return None

    # MT5 서버 시간 확인
    to_date = mt5.symbol_info_tick("BITCOIN").time
    from_date = to_date - 60*60*24*days
    server_time = datetime.utcfromtimestamp(to_date)
    print(f"MT5 서버 시간: {server_time}")

    # 조회 시작 시간 설정
    #from_date = server_time - timedelta(days=days)
    #to_date = server_time
    
    print(f"조회 시작 시간: {datetime.utcfromtimestamp(from_date)}")
    print(f"조회 종료 시간: {datetime.utcfromtimestamp(to_date)}")
    
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
    
    mt5.shutdown()
    return df

def analyze_trades(df):
    print("\n거래 분석:")
    print(f"총 거래 수: {len(df)}")
    
    print("\n심볼별 거래 수:")
    symbol_counts = df['symbol'].value_counts()
    print(symbol_counts)
    
    print("\n가장 빈번하게 거래된 심볼:")
    print(symbol_counts.index[0])
    
    print(f"\n가장 큰 거래량: {df['volume'].max()}")
    
    print("\n진입/청산 비율:")
    entry_counts = df['entry'].value_counts()
    print(entry_counts)
    
    print("\n총 수익:")
    print(df['profit'].sum())

def analyze_positions(positions):
    total_trades = len(positions)
    winning_trades = positions[positions['profit'] > 0]
    losing_trades = positions[positions['profit'] <= 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    loss_rate = 1 - win_rate
    
    avg_profit = winning_trades['profit'].mean() if not winning_trades.empty else 0
    avg_loss = abs(losing_trades['profit'].mean()) if not losing_trades.empty else 0
    
    te = win_rate * avg_profit - loss_rate * avg_loss
    rr = avg_profit / avg_loss if avg_loss != 0 else float('inf')
    win_rr = loss_rate / win_rate if win_rate != 0 else float('inf')
    
    return {
        '트레이딩 횟수': total_trades,
        '승률': win_rate,
        '패율': loss_rate,
        '평균수익': avg_profit,
        '평균손실': avg_loss,
        'TE': te,
        'R/R': rr,
        'Win R/R': win_rr
    }

def analyze_by_symbol(df):
    """
    심볼별로 거래를 분석하는 함수
    
    Args:
        df (pd.DataFrame): 전체 거래 내역 DataFrame
    
    Returns:
        pd.DataFrame: 심볼별 분석 결과
    """
    symbols = df['symbol'].unique()
    results = []
    
    for symbol in symbols:
        symbol_df = df[df['symbol'] == symbol]
        symbol_analysis = analyze_positions(symbol_df)
        symbol_analysis['심볼'] = symbol
        results.append(symbol_analysis)
    
    result_df = pd.DataFrame(results)
    # '심볼' 열을 첫 번째 열로 이동
    cols = ['심볼'] + [col for col in result_df.columns if col != '심볼']
    return result_df[cols]

def analyze_closed_positions(file_path):
    # Closed Positions 시트 읽기
    df = pd.read_excel(file_path, sheet_name='Closed Positions')
    
    # 전체 분석
    all_analysis = analyze_positions(df)
    
    # 롱 포지션 분석 (청산이 Sell인 경우)
    long_positions = df[df['type'] == 1]  # Sell로 청산된 거래
    long_analysis = analyze_positions(long_positions)
    
    # 숏 포지션 분석 (청산이 Buy인 경우)
    short_positions = df[df['type'] == 0]  # Buy로 청산된 거래
    short_analysis = analyze_positions(short_positions)
    
    # 심볼별 분석
    symbol_analysis = analyze_by_symbol(df)
    
    # 결과를 DataFrame으로 생성
    result = pd.DataFrame({
        '구분': ['전체', '롱 포지션', '숏 포지션'],
        '트레이딩 횟수': [all_analysis['트레이딩 횟수'], long_analysis['트레이딩 횟수'], short_analysis['트레이딩 횟수']],
        '승률': [all_analysis['승률'], long_analysis['승률'], short_analysis['승률']],
        '패율': [all_analysis['패율'], long_analysis['패율'], short_analysis['패율']],
        '평균수익': [all_analysis['평균수익'], long_analysis['평균수익'], short_analysis['평균수익']],
        '평균손실': [all_analysis['평균손실'], long_analysis['평균손실'], short_analysis['평균손실']],
        'TE': [all_analysis['TE'], long_analysis['TE'], short_analysis['TE']],
        'R/R': [all_analysis['R/R'], long_analysis['R/R'], short_analysis['R/R']],
        'Win R/R': [all_analysis['Win R/R'], long_analysis['Win R/R'], short_analysis['Win R/R']]
    })
    
    # 결과를 엑셀 파일에 저장
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
        result.to_excel(writer, sheet_name='Analysis Result', index=False)
        symbol_analysis.to_excel(writer, sheet_name='Symbol Analysis', index=False)
    
    print("분석 결과가 'Analysis Result' 시트에 저장되었습니다.")
    print("심볼별 분석 결과가 'Symbol Analysis' 시트에 저장되었습니다.")

def process_excel_file(file_path):
    """
    저장된 엑셀 파일을 처리하는 함수
    
    Args:
        file_path (str): 엑셀 파일 경로
    """
    # 엑셀 파일 읽기
    df = pd.read_excel(file_path)
    
    # 포지션 ID별로 그룹화하고 entry가 0과 1 둘 다 있는 경우만 유지
    complete_positions = df.groupby('position_id').filter(lambda x: set(x['entry']) == {0, 1})
    
    # 삭제된 행들 (불완전한 포지션)
    incomplete_positions = df[~df.index.isin(complete_positions.index)]
    
    # Complete Position에서 Entry가 Out(청산) 내역만 추출
    closed_positions = complete_positions[complete_positions['entry'] == 1]
    
    # 결과를 엑셀 파일에 저장
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
        complete_positions.to_excel(writer, sheet_name='Complete Positions', index=False)
        incomplete_positions.to_excel(writer, sheet_name='Incomplete Positions', index=False)
        closed_positions.to_excel(writer, sheet_name='Closed Positions', index=False)
    
    print(f"처리된 엑셀 파일이 {file_path}에 저장되었습니다.")
    print(f"완전한 포지션 수: {len(complete_positions)//2}")
    print(f"불완전한 포지션 수: {len(incomplete_positions)}")
    print(f"청산된 포지션 수: {len(closed_positions)}")

    # Closed Positions 분석
    analyze_closed_positions(file_path)

def save_to_excel(df, magic_number):
    """
    거래 내역을 엑셀 파일로 저장하는 함수

    Args:
        df (pd.DataFrame): 저장할 DataFrame
        magic_number (int): 매직 넘버
    """
    if df.empty:
        print("저장할 거래 내역이 없습니다.")
        return

    # 첫 거래와 마지막 거래 시간 가져오기
    first_trade_time = df['time'].min().strftime('%Y%m%d_%H%M%S')
    last_trade_time = df['time'].max().strftime('%Y%m%d_%H%M%S')

    filename = f"Trading_History_{magic_number}_{first_trade_time}_{last_trade_time}.xlsx"
    
    # 현재 스크립트의 디렉토리 경로를 얻습니다
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로를 생성합니다
    file_path = os.path.join(script_dir, filename)
    
    # DataFrame을 엑셀 파일로 저장합니다
    df.to_excel(file_path, index=False, engine='openpyxl', sheet_name='All Trades')
    print(f"거래 내역이 {file_path} 파일로 저장되었습니다.")
    
    # 저장된 엑셀 파일 처리
    process_excel_file(file_path)

if __name__ == "__main__":
    trades = get_recent_trades(magic_number=241028, days=7)
    if trades is not None:
        print("\n매직 넘버 81009의 거래 내역:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(trades)
        
        analyze_trades(trades)
        
        # 엑셀 파일로 저장
        save_to_excel(trades, 241028)
    else:
        print("거래 내역을 가져오는데 실패했습니다.")
