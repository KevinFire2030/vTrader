import sys
import os

# 현재 스크립트의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 (backtest 폴더의 상위 디렉토리)
project_root = os.path.dirname(current_dir)
# mt5_backtrader 폴더 경로
mt5_backtrader_path = os.path.join(project_root, 'mt5_backtrader')

# 시스템 경로에 mt5_backtrader 폴더를 추가
sys.path.insert(0, mt5_backtrader_path)



# mt5_backtrader에서 backtrader를 import
import backtrader as bt

# backtrader의 위치 출력
print(f"\nUsing Backtrader from: {bt.__file__}")

from backtrader import analyzers as btanalyzers



import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz
import numpy as np

class TestStrategy(bt.Strategy):
    params = (
        ('stake', 0.01),  # 거래 단위를 0.01로 설정 (0.01 lot)
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.trades = []  # 거래 내역을 저장할 리스트
        
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'Date': self.data.datetime.datetime(0),
                'Type': 'Buy' if trade.size > 0 else 'Sell',
                'Price': trade.price,
                'Size': abs(trade.size),
                'Value': abs(trade.value),
                'Commission': trade.commission,
                'PnL': trade.pnl
            })
            
            print(f'\n거래 종료:')
            print(f'날짜: {self.data.datetime.datetime(0)}')
            print(f'유형: {"Buy" if trade.size > 0 else "Sell"}')
            print(f'가격: {trade.price:.5f}')
            print(f'수량: {abs(trade.size)}')
            print(f'수수료: {trade.commission:.5f}')
            print(f'손익: {trade.pnl:.5f}')
    
    def notify_order(self, order):  # 주문 상태 확인을 위한 메서드 추가
        if order.status in [order.Submitted, order.Accepted]:
            return  # 주문이 제출되거나 수락된 상태
            
        if order.status in [order.Completed]:  # 주문 완료
            if order.isbuy():
                print(f'매수 체결: 가격: {order.executed.price:.5f}, 수량: {order.executed.size}')
            else:
                print(f'매도 체결: 가격: {order.executed.price:.5f}, 수량: {order.executed.size}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f'주문 실패: {order.status}')
        
    def next(self):
        # 디버깅을 위한 출력
        print(f'\n현재 시간: {self.data.datetime.datetime(0)}')
        print(f'현재 종가: {self.dataclose[0]:.5f}')
        print(f'이전 종가: {self.dataclose[-1]:.5f}')
        print(f'현재 포지션: {self.position.size}')
        print(f'현재 현금: {self.broker.get_cash():.2f}')
        
        if not self.position:  # 포지션이 없을 때
            if self.dataclose[0] > self.dataclose[-1]:
                print('매수 신호!')
                self.buy(size=self.params.stake)  # 거래 크기 지정
        elif self.dataclose[0] < self.dataclose[-1]:
            print('매도 신호!')
            self.sell(size=self.params.stake)  # 거래 크기 지정

class TradeAnalyzer(bt.Analyzer):
    def __init__(self):
        self.trades = []
        self.total_trades = 0
        self.won = 0
        self.lost = 0
        self.total_won = 0.0
        self.total_lost = 0.0

    def notify_trade(self, trade):
        if trade.isclosed:
            self.total_trades += 1
            if trade.pnl > 0:
                self.won += 1
                self.total_won += trade.pnl
            else:
                self.lost += 1
                self.total_lost -= trade.pnl  # 손실은 음수이므로 부호 변경

    def get_analysis(self):
        # 승률 계산
        win_rate = self.won / self.total_trades if self.total_trades > 0 else 0
        loss_rate = 1 - win_rate  # 패율

        # 평균 수익/손실 계산
        avg_won = self.total_won / self.won if self.won > 0 else 0
        avg_lost = self.total_lost / self.lost if self.lost > 0 else 0

        # R/R과 Win R/R 계산
        rr = avg_won / avg_lost if avg_lost > 0 else float('inf')
        win_rr = loss_rate / win_rate if win_rate > 0 else float('inf')

        # TE 계산
        te = win_rate * avg_won - loss_rate * avg_lost

        return {
            'total_trades': self.total_trades,
            'win_rate': win_rate,
            'loss_rate': loss_rate,
            'avg_won': avg_won,
            'avg_lost': avg_lost,
            'rr': rr,
            'win_rr': win_rr,
            'te': te
        }

def get_mt5_data(symbol, timeframe, start_date, end_date):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # 심볼 정보 확인
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"심볼 {symbol}을(를) 찾을 수 없습니다.")
        return None

    # 심볼이 선택되어 있는지 확인
    if not symbol_info.select:
        print(f"심볼 {symbol}이(가) Market Watch에 없습니다. 추가를 시도합니다.")
        if not mt5.symbol_select(symbol, True):
            print(f"심볼 {symbol} 추가 실패")
            return None

    # 서버 시간(UTC+3)을 UTC로 변환
    utc_from = start_date + timedelta(hours=9)
    utc_to = end_date + timedelta(hours=9)

    print(f"요청 시작 시간 (서버): {start_date}")
    print(f"요청 종료 시간 (서버): {end_date}")
    print(f"요청 시작 시간 (UTC): {utc_from}")
    print(f"요청 종료 시간 (UTC): {utc_to}")

    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        print(f"심볼 {symbol}의 데이터를 가져오는데 실패했습니다.")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    print(f"가져온 데이터 기간: {df.index[0]} ~ {df.index[-1]}")
    print(f"총 데이터 수: {len(df)}")
    
    return df

if __name__ == '__main__':
    symbol = "#USNDAQ100"
    timeframe = mt5.TIMEFRAME_M30

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 10, 25)

    data = get_mt5_data(symbol, timeframe, start_date, end_date)

    if data is not None and not data.empty:
        cerebro = bt.Cerebro()

        feed = bt.feeds.PandasData(
            dataname=data,
            datetime=None,
        )
        cerebro.adddata(feed)

        cerebro.addstrategy(TestStrategy)
        
        # 브로커 설정
        cerebro.broker.setcash(100000.0)
        comminfo = bt.CommissionInfo(
            commission=0.001,
            leverage=500,
            automargin=True
        )
        cerebro.broker.addcommissioninfo(comminfo)

        # Analyzer 추가
        cerebro.addanalyzer(TradeAnalyzer, _name='trade_analyzer')

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        results = cerebro.run()
        strat = results[0]
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # 분석 결과 출력
        analysis = strat.analyzers.trade_analyzer.get_analysis()
        print('\n거래 분석:')
        print(f"총 거래 횟수: {analysis['total_trades']}")
        print(f"승률: {analysis['win_rate']:.2%}")
        print(f"평균 수익: {analysis['avg_won']:.2f}")
        print(f"평균 손실: {analysis['avg_lost']:.2f}")
        print(f"R/R: {analysis['rr']:.2f}")
        print(f"Win R/R: {analysis['win_rr']:.2f}")
        print(f"TE: {analysis['te']:.2f}")

        # 거래 내역 저장
        if strat.trades:
            df = pd.DataFrame(strat.trades)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_name = 'backtest_trades.xlsx'
            file_path = os.path.join(script_dir, file_name)
            df.to_excel(file_path, index=False)
            print(f"\n거래 내역이 '{file_path}'에 저장되었습니다.")
