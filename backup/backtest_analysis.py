import pandas as pd
import os
from datetime import datetime
import pytz

def read_report_excel(filename):
    """
    ReportTester Excel 파일을 읽어옵니다.
    
    :param filename: Excel 파일 이름
    :return: 거래 내역이 담긴 DataFrame
    """
    try:
        # 현재 스크립트의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 파일의 전체 경로 생성
        file_path = os.path.join(current_dir, filename)
        
        # Excel 파일 읽기
        df = pd.read_excel(file_path)
        
        print(f"총 {len(df)}개의 거래 내역을 읽었습니다.")
        return df
    
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {filename}")
        print(f"현재 작업 디렉토리: {os.getcwd()}")
        return None
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

def filter_closed_trades(df):
    """
    청산된 거래만 필터링합니다.
    
    :param df: 전체 거래 내역이 담긴 DataFrame
    :return: 청산된 거래만 담긴 DataFrame
    """
    return df[df['Direction'] == 'out']

def analyze_trades(df):
    """
    거래 내역을 분석합니다.
    
    :param df: 거래 내역이 담긴 DataFrame
    :return: 분석 결과 딕셔너리
    """
    # 총 포지션 청산 횟수
    total_closed = len(df)
    
    # 롱포지션과 숏포지션 청산 횟수
    long_closed = len(df[df['Type'] == 'sell'])
    short_closed = len(df[df['Type'] == 'buy'])
    
    # 수익 거래와 손실 거래 분리
    profitable_trades = df[df['Profit'] > 0]
    losing_trades = df[df['Profit'] <= 0]
    
    # 승률 계산
    win_rate = len(profitable_trades) / total_closed if total_closed > 0 else 0
    
    # 평균 수익과 평균 손실 계산
    avg_profit = profitable_trades['Profit'].mean() if len(profitable_trades) > 0 else 0
    avg_loss = abs(losing_trades['Profit'].mean()) if len(losing_trades) > 0 else 0
    
    # RR비율 계산
    rr_ratio = avg_profit / avg_loss if avg_loss != 0 else float('inf')
    
    # 기대값 TE 계산
    te = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
    
    # 결과 딕셔너리 생성
    results = {
        "총 포지션 청산 횟수": total_closed,
        "롱포지션 청산": long_closed,
        "숏포지션 산": short_closed,
        "승률": win_rate,
        "평균 수익": avg_profit,
        "평균 손실": avg_loss,
        "RR비율": rr_ratio,
        "기대값 TE": te
    }
    
    return results

def analyze_trades_by_time(df):
    """
    시간대별로 거래 성과를 분석합니다.
    
    :param df: 거래 내역이 담긴 DataFrame
    :return: 시간대별 분석 결과가 담긴 DataFrame
    """
    # DataFrame 복사본 생성
    df = df.copy()
    
    print("DataFrame 열 이름:", df.columns.tolist())
    
    # 'Time' 열을 datetime 형식으로 변환
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time'])
    else:
        print("'Time' 열을 찾을 수 없습니다.")
        return pd.DataFrame()
    
    # 모스크바 시간대 설정
    moscow_tz = pytz.timezone('Europe/Moscow')
    df['Time'] = df['Time'].dt.tz_localize(moscow_tz)
    
    # 뉴욕 시간대로 변환
    ny_tz = pytz.timezone('America/New_York')
    df['NY_Time'] = df['Time'].dt.tz_convert(ny_tz)
    
    # 모스크바 시간대별로 그룹화
    df['Moscow_hour'] = df['Time'].dt.hour
    
    # 뉴욕 시간대별로 그룹화
    df['NY_hour'] = df['NY_Time'].dt.hour
    
    # 'Profit' 열 확인
    if 'Profit' not in df.columns:
        print(f"'Profit' 열을 찾을 수 없습니다. 사용 가능한 열: {df.columns.tolist()}")
        return pd.DataFrame()
    
    results = []
    for hour in range(24):
        moscow_group = df[df['Moscow_hour'] == hour]
        ny_group = df[df['NY_hour'] == hour]
        
        moscow_trades = len(moscow_group)
        moscow_profitable = len(moscow_group[moscow_group['Profit'] > 0])
        moscow_win_rate = moscow_profitable / moscow_trades if moscow_trades > 0 else 0
        moscow_total_profit = moscow_group['Profit'].sum()
        
        ny_trades = len(ny_group)
        ny_profitable = len(ny_group[ny_group['Profit'] > 0])
        ny_win_rate = ny_profitable / ny_trades if ny_trades > 0 else 0
        ny_total_profit = ny_group['Profit'].sum()
        
        results.append({
            '시간대 (모스크바)': f"{hour:02d}:00-{(hour+1)%24:02d}:00",
            '거래 횟수 (모스크바)': moscow_trades,
            '승률 (모스크바)': moscow_win_rate,
            '총 수익 (모스크바)': moscow_total_profit,
            '시간대 (뉴욕)': f"{hour:02d}:00-{(hour+1)%24:02d}:00",
            '거래 횟수 (뉴욕)': ny_trades,
            '승률 (뉴욕)': ny_win_rate,
            '총 수익 (뉴욕)': ny_total_profit
        })
    
    return pd.DataFrame(results)

def analyze_trades_by_time_range(df, start_hour, end_hour):
    """
    특정 시간대의 거래만 분석합니다.
    
    :param df: 거래 내역이 담긴 DataFrame
    :param start_hour: 시작 시간 (0-23)
    :param end_hour: 종료 시간 (0-23)
    :return: 분석 결과 딕셔너리
    """
    # DataFrame 복사
    df = df.copy()
    
    # 'Time' 열을 datetime 형식으로 변환
    df['Time'] = pd.to_datetime(df['Time'])
    
    # 뉴욕 시간대로 변환
    ny_tz = pytz.timezone('America/New_York')
    df['NY_Time'] = df['Time'].dt.tz_localize(None).dt.tz_localize('UTC').dt.tz_convert(ny_tz)
    
    # 지정된 시간대의 거래만 필터링
    df_filtered = df[(df['NY_Time'].dt.hour >= start_hour) & (df['NY_Time'].dt.hour < end_hour)]
    
    # 분석 수행
    total_trades = len(df_filtered)
    
    if total_trades == 0:
        return {
            "총 거래 횟수": 0,
            "승률": 0,
            "평균 수익": 0,
            "평균 손실": 0,
            "RR비율": 0,
            "기대값 TE": 0
        }
    
    profitable_trades = len(df_filtered[df_filtered['Profit'] > 0])
    win_rate = profitable_trades / total_trades if total_trades > 0 else 0
    
    avg_profit = df_filtered[df_filtered['Profit'] > 0]['Profit'].mean() if profitable_trades > 0 else 0
    avg_loss = abs(df_filtered[df_filtered['Profit'] <= 0]['Profit'].mean()) if (total_trades - profitable_trades) > 0 else 0
    
    rr_ratio = avg_profit / avg_loss if avg_loss != 0 else float('inf')
    te = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)
    
    return {
        "총 거래 횟수": total_trades,
        "승률": win_rate,
        "평균 수익": avg_profit,
        "평균 손실": avg_loss,
        "RR비율": rr_ratio,
        "기대값 TE": te
    }

if __name__ == "__main__":
    filename = "ReportTester-590056583_2.xlsx"
    trade_history = read_report_excel(filename)
    
    if trade_history is not None:
        closed_trades = filter_closed_trades(trade_history)
        print(f"\n총 {len(closed_trades)}개의 청산된 거래를 필터링했습니다.")
        
        print("\n청산 내역 샘플:")
        print(closed_trades.head())
        
        analysis_results = analyze_trades(closed_trades)
        
        print("\n거래 분석 결과:")
        for key, value in analysis_results.items():
            if key in ["총 포지션 청산 횟수", "롱포지션 청산", "숏포지션 산"]:
                print(f"{key}: {value}회")
            elif key == "승률":
                win_rate = value
                rr_ratio = analysis_results["RR비율"]
                breakeven_rr = (1 - win_rate) / win_rate
                print(f"{key}: {value:.2%} (RR비율 > {breakeven_rr:.2f})")
            elif key in ["평균 수익", "평균 손실", "기대값 TE"]:
                print(f"{key}: ${value:.2f}")
            elif key == "RR비율":
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
        # 시간대별 분석 결과 출력
        time_analysis = analyze_trades_by_time(closed_trades)
        if not time_analysis.empty:
            print("\n모든 시간대 거래 분석 결과:")
            pd.set_option('display.float_format', '{:.2%}'.format)
            
            # 거래가 있는 시간대만 필터링
            active_times = time_analysis[time_analysis['거래 횟수 (뉴욕)'] > 0]
            
            # 승률 기준으로 내림차순 정렬
            active_times = active_times.sort_values('승률 (뉴욕)', ascending=False)
            
            print(active_times[['시간대 (뉴욕)', '거래 횟수 (뉴욕)', '승률 (뉴욕)', '총 수익 (뉴욕)']].to_string(index=False))
            pd.reset_option('display.float_format')
            
            # 승률이 가장 높은 시간대 선택
            best_time_range = active_times.iloc[0]['시간대 (뉴욕)']
            start_hour, end_hour = map(int, best_time_range.split('-')[0].split(':'))
            
            # 선택된 시간대의 거래 분석
            best_time_analysis = analyze_trades_by_time_range(closed_trades, start_hour, end_hour)
            
            print(f"\n{best_time_range} (뉴욕 시간) 시간대 거래 분석 결과:")
            for key, value in best_time_analysis.items():
                if key in ["총 거래 횟수"]:
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
            print("\n시간대별 분석을 수행할 수 없습니다.")
    else:
        print("거래 내역을 분석할 수 없습니다.")
