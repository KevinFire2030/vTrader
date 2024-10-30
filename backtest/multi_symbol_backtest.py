import sys
import os

# 현재 스크립트의 디렉토리
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리
project_root = os.path.dirname(current_dir)
# mt5_backtrader 폴더 경로
mt5_backtrader_path = os.path.join(project_root, 'mt5_backtrader')

# 시스템 경로에 mt5_backtrader 폴더를 추가
sys.path.insert(0, mt5_backtrader_path)

# mt5_backtrader에서 backtrader를 import
import backtrader as bt
from backtrader import analyzers as btanalyzers
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz
import numpy as np

def get_mt5_data(symbols, timeframe, start_date, end_date):
    """여러 심볼의 데이터를 동시에 가져오는 함수"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    # UTC 시간으로 변환
    utc_from = start_date + timedelta(hours=9)
    utc_to = end_date + timedelta(hours=9)

    print(f"요청 시작 시간 (서버): {start_date}")
    print(f"요청 종료 시간 (서버): {end_date}")

    data_dict = {}
    common_index = None

    # 각 심볼의 데이터 가져오기
    for symbol in symbols:
        # 심볼 정보 확인
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"심볼 {symbol}을(를) 찾을 수 없습니다.")
            continue

        # 심볼이 선택되어 있는지 확인
        if not symbol_info.select:
            print(f"심볼 {symbol}이(가) Market Watch에 없습니다. 추가를 시도합니다.")
            if not mt5.symbol_select(symbol, True):
                print(f"심볼 {symbol} 추가 실패")
                continue

        rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
        if rates is None or len(rates) == 0:
            print(f"심볼 {symbol}의 데이터를 가져오는데 실패했습니다.")
            continue

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        # 첫 번째 심볼의 인덱스를 기준으로 설정
        if common_index is None:
            common_index = df.index
        else:
            # 공통된 시간대만 유지
            common_index = common_index.intersection(df.index)

        data_dict[symbol] = df

    # 모든 데이터프레임을 공통 인덱스로 리샘플링
    for symbol in data_dict:
        data_dict[symbol] = data_dict[symbol].reindex(common_index)
        print(f"{symbol} 데이터: {len(data_dict[symbol])} 개")

    mt5.shutdown()
    return data_dict

def get_watchlist_symbols():
    """MT5의 Market Watch에서 visible한 심볼들을 가져오는 함수"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return []
    
    symbols = []
    for symbol in mt5.symbols_get():
        # visible 속성이 True인 심볼만 선택
        if symbol.visible and len(symbols) < 10:  # 최대 10개
            symbols.append(symbol.name)
    
    mt5.shutdown()
    print(f"Market Watch에서 visible한 심볼: {symbols}")
    return symbols

class MultiSymbolStrategy(bt.Strategy):
    params = (
        ('stake', 0.01),  # 거래 단위를 0.01로 설정 (0.01 lot)
    )
    
    def __init__(self):
        self.orders = {}  # 각 데이터피드별 주문 추적
        self.trades = []  # 거래 내역을 저장할 리스트
        
        # 각 데이터피드(심볼)별로 종가 저장
        self.dataclose = {}
        for data in self.datas:
            self.dataclose[data._name] = data.close
            
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'Date': self.data.datetime.datetime(0),
                'Symbol': trade.data._name,
                'Type': 'Buy' if trade.size > 0 else 'Sell',
                'Price': trade.price,
                'Size': abs(trade.size),
                'Value': abs(trade.value),
                'Commission': trade.commission,
                'PnL': trade.pnl
            })
            
            print(f'\n거래 종료:')
            print(f'심볼: {trade.data._name}')
            print(f'날짜: {self.data.datetime.datetime(0)}')
            print(f'유형: {"Buy" if trade.size > 0 else "Sell"}')
            print(f'��격: {trade.price:.5f}')
            print(f'수량: {abs(trade.size)}')
            print(f'수수료: {trade.commission:.5f}')
            print(f'손익: {trade.pnl:.5f}')
    
    def next(self):
        # 각 심볼별로 전략 실행
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            
            print(f'\n심볼: {symbol}')
            print(f'현재 시간: {data.datetime.datetime(0)}')
            print(f'현재 종가: {self.dataclose[symbol][0]:.5f}')
            print(f'이전 종가: {self.dataclose[symbol][-1]:.5f}')
            print(f'현재 포지션: {pos.size if pos else 0}')
            
            # 단순 전략: 전날 종가보다 오늘 종가가 높으면 매수, 낮으면 매도
            if not pos:  # 포지션이 없을 때
                if self.dataclose[symbol][0] > self.dataclose[symbol][-1]:
                    print(f'{symbol} 매수 신호!')
                    self.buy(data=data, size=self.params.stake)
            else:  # 포지션이 있을 때
                if self.dataclose[symbol][0] < self.dataclose[symbol][-1]:
                    print(f'{symbol} 매도 신호!')
                    self.sell(data=data, size=self.params.stake)

class TradeAnalyzer(bt.Analyzer):
    def __init__(self):
        self.symbols = {}  # 각 심볼별 거래 정보를 저장할 딕셔너리
        
    def notify_trade(self, trade):
        if trade.isclosed:
            symbol = trade.data._name
            
            # 심볼이 처음 등장하면 초기화
            if symbol not in self.symbols:
                self.symbols[symbol] = {
                    'trades': [],
                    'total_trades': 0,
                    'won': 0,
                    'lost': 0,
                    'total_won': 0.0,
                    'total_lost': 0.0
                }
            
            # 거래 정보 업데이트
            self.symbols[symbol]['total_trades'] += 1
            if trade.pnl > 0:
                self.symbols[symbol]['won'] += 1
                self.symbols[symbol]['total_won'] += trade.pnl
            else:
                self.symbols[symbol]['lost'] += 1
                self.symbols[symbol]['total_lost'] -= trade.pnl  # 손실은 음수이므로 부호 변경

    def get_analysis(self):
        # 전체 결과를 저장할 딕셔너리
        total_result = {
            'total_trades': 0,
            'total_won': 0,
            'total_lost': 0,
            'won': 0,
            'lost': 0,
            'symbols': {}
        }
        
        # 각 심볼별 분석
        for symbol, data in self.symbols.items():
            # 승률 계산
            win_rate = data['won'] / data['total_trades'] if data['total_trades'] > 0 else 0
            loss_rate = 1 - win_rate
            
            # 평균 수익/손실 계산
            avg_won = data['total_won'] / data['won'] if data['won'] > 0 else 0
            avg_lost = data['total_lost'] / data['lost'] if data['lost'] > 0 else 0
            
            # R/R과 Win R/R 계산
            rr = avg_won / avg_lost if avg_lost > 0 else float('inf')
            win_rr = loss_rate / win_rate if win_rate > 0 else float('inf')
            
            # TE 계산
            te = win_rate * avg_won - loss_rate * avg_lost
            
            # 심볼별 결과 저장
            total_result['symbols'][symbol] = {
                'total_trades': data['total_trades'],
                'win_rate': win_rate,
                'loss_rate': loss_rate,
                'avg_won': avg_won,
                'avg_lost': avg_lost,
                'rr': rr,
                'win_rr': win_rr,
                'te': te
            }
            
            # 전체 통계 업데이트
            total_result['total_trades'] += data['total_trades']
            total_result['total_won'] += data['total_won']
            total_result['total_lost'] += data['total_lost']
            total_result['won'] += data['won']
            total_result['lost'] += data['lost']
        
        # 전체 승률 계산
        if total_result['total_trades'] > 0:
            total_result['win_rate'] = total_result['won'] / total_result['total_trades']
            total_result['loss_rate'] = 1 - total_result['win_rate']
            total_result['avg_won'] = total_result['total_won'] / total_result['won'] if total_result['won'] > 0 else 0
            total_result['avg_lost'] = total_result['total_lost'] / total_result['lost'] if total_result['lost'] > 0 else 0
            total_result['rr'] = total_result['avg_won'] / total_result['avg_lost'] if total_result['avg_lost'] > 0 else float('inf')
            total_result['win_rr'] = total_result['loss_rate'] / total_result['win_rate'] if total_result['win_rate'] > 0 else float('inf')
            total_result['te'] = total_result['win_rate'] * total_result['avg_won'] - total_result['loss_rate'] * total_result['avg_lost']
        
        return total_result

if __name__ == '__main__':
    timeframe = mt5.TIMEFRAME_D1
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 10, 25)

    # Market Watch에서 선택된 심볼들 가져오기
    symbols = get_watchlist_symbols()
    print(f"Market Watch에서 선택된 심볼: {symbols}")

    if symbols:
        # 여러 심볼의 데이터를 동시에 가져오기
        data_dict = get_mt5_data(symbols, timeframe, start_date, end_date)

        if data_dict:
            cerebro = bt.Cerebro()

            # 각 심볼에 대한 데이터 추가
            for symbol in data_dict:
                feed = bt.feeds.PandasData(
                    dataname=data_dict[symbol],
                    datetime=None,
                    name=symbol
                )
                cerebro.adddata(feed)
                print(f"{symbol} 데이터 추가 완료")

            cerebro.addstrategy(MultiSymbolStrategy)
            
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
            
            # 전체 포트폴리오 분석 결과
            print('\n전체 포트폴리오 분석:')
            print(f"총 거래 횟수: {analysis['total_trades']}")
            print(f"승률: {analysis['win_rate']:.2%}")
            print(f"평균 수익: {analysis['avg_won']:.2f}")
            print(f"평균 손실: {analysis['avg_lost']:.2f}")
            print(f"R/R: {analysis['rr']:.2f}")
            print(f"Win R/R: {analysis['win_rr']:.2f}")
            print(f"TE: {analysis['te']:.2f}")

            # 심볼별 분석 결과
            print('\n심볼별 분석:')
            for symbol, stats in analysis['symbols'].items():
                print(f"\n{symbol}:")
                print(f"  거래 횟수: {stats['total_trades']}")
                print(f"  승률: {stats['win_rate']:.2%}")
                print(f"  평균 수익: {stats['avg_won']:.2f}")
                print(f"  평균 손실: {stats['avg_lost']:.2f}")
                print(f"  R/R: {stats['rr']:.2f}")
                print(f"  Win R/R: {stats['win_rr']:.2f}")
                print(f"  TE: {stats['te']:.2f}")

            # 거래 내역을 엑셀로 저장
            if strat.trades:
                df = pd.DataFrame(strat.trades)
                script_dir = os.path.dirname(os.path.abspath(__file__))
                file_name = 'multi_symbol_trades.xlsx'
                file_path = os.path.join(script_dir, file_name)
                
                # 엑셀 파일에 시트 추가
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # 전체 거래 내역
                    df.to_excel(writer, sheet_name='All Trades', index=False)
                    
                    # 심볼별 거래 내역
                    for symbol in symbols:
                        symbol_trades = df[df['Symbol'] == symbol]
                        if not symbol_trades.empty:
                            symbol_trades.to_excel(writer, sheet_name=f'{symbol} Trades', index=False)
                
                print(f"\n거래 내역이 '{file_path}'에 저장되었습니다.")


