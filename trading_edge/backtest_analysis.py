import pandas as pd
import numpy as np

def read_report_excel(filename):
    """
    ReportTester Excel 파일을 읽어옵니다.
    
    :param filename: Excel 파일 이름
    :return: 거래 내역이 담긴 DataFrame
    """
    try:
        # Excel 파일 읽기
        df = pd.read_excel(filename)
        
        # 열 이름 변경 (필요한 경우)
        column_mapping = {
            'Time': '시간',
            'Deal': '거래',
            'Symbol': '심볼',
            'Type': '유형',
            'Direction': '방향',
            'Volume': '거래량',
            'Price': '가격',
            'Order': '주문',
            'Commission': '수수료',
            'Swap': '스왑',
            'Profit': '손익',
            'Balance': '잔고',
            'Comment': '코멘트'
        }
        df = df.rename(columns=column_mapping)
        
        # 시간 데이터 변환
        df['시간'] = pd.to_datetime(df['시간'])
        
        print(f"총 {len(df)}개의 거래 내역을 읽었습니다.")
        return df
    
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

def analyze_closed_trades(df):
    """
    청산 내역을 분석합니다.
    
    :param df: 거래 내역이 담긴 DataFrame
    :return: 분석 결과 딕셔너리
    """
    # 청산된 거래만 필터링 (손익이 0이 아닌 거래)
    closed_trades = df[df['손익'] != 0]
    
    # 총 포지션 청산 횟수
    total_closed = len(closed_trades)
    
    # 롱포지션과 숏포지션 청산 횟수
    long_closed = len(closed_trades[closed_trades['유형'] == 'sell'])
    short_closed = len(closed_trades[closed_trades['유형'] == 'buy'])
    
    # 수익 거래와 손실 거래 분리
    profitable_trades = closed_trades[closed_trades['손익'] > 0]
    losing_trades = closed_trades[closed_trades['손익'] < 0]
    
    # 승률 계산
    win_rate = len(profitable_trades) / total_closed if total_closed > 0 else 0
    
    # 평균 수익과 평균 손실 계산
    avg_profit = profitable_trades['손익'].mean() if len(profitable_trades) > 0 else 0
    avg_loss = abs(losing_trades['손익'].mean()) if len(losing_trades) > 0 else 0
    
    # RR비율 계산
    rr_ratio = avg_profit / avg_loss if avg_loss != 0 else np.inf
    
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
    filename = "ReportTester-590056583.xlsx"
    trade_history = read_report_excel(filename)
    
    if trade_history is not None:
        print("\n거래 내역 샘플:")
        print(trade_history.head())
        
        print("\n기본 통계:")
        print(trade_history.describe())
        
        # 청산 내역 분석
        analysis_results = analyze_closed_trades(trade_history)
        
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
