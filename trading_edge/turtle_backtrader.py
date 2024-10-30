import backtrader as bt
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import pytz

# MT5 연결
if not mt5.initialize():
    print("MT5 초기화 실패")
    mt5.shutdown()
    quit()

class SymbolData(bt.feeds.PandasData):
    params = (
        ('pip_value', 1),
    )

class MovingAverageCrossStrategy(bt.Strategy):
    params = (
        ('fast_length', 10),
        ('slow_length', 20),
        ('atr_period', 20),
    )

    def __init__(self):
        self.fast_ma = {}
        self.slow_ma = {}
        self.atr = {}
        self.order = None
        self.trades = []
        for data in self.datas:
            self.fast_ma[data._name] = bt.indicators.SMA(data, period=self.params.fast_length)
            self.slow_ma[data._name] = bt.indicators.SMA(data, period=self.params.slow_length)
            self.atr[data._name] = bt.indicators.ATR(data, period=self.params.atr_period)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
        self.trades.append({
            'symbol': trade.data._name,
            'size': trade.size,
            'entry_price': trade.price,
            'exit_price': trade.data.close[0],  # 현재 종가를 청산가로 사용
            'value': trade.value,
            'pnl': trade.pnl,
            'pnlcomm': trade.pnlcomm,
            'commission': trade.commission,
        })

    def next(self):
        for data in self.datas:
            if not self.getposition(data):
                if self.fast_ma[data._name] > self.slow_ma[data._name]:
                    size = self.get_turtle_unit(data)
                    self.buy(data=data, size=size)
            else:
                if self.fast_ma[data._name] < self.slow_ma[data._name]:
                    self.close(data=data)

    def get_turtle_unit(self, data):
        if len(self.atr[data._name]) > 0:
            risk = self.broker.get_cash() * 0.01  # 1% 리스크
            atr_value = self.atr[data._name][0]
            if atr_value != 0:
                unit = risk / (atr_value * data.params.pip_value)
                return unit
        return 0

def get_mt5_data(symbol, timeframe, start_date, end_date):
    timezone = pytz.timezone("Etc/UTC")
    start_date = datetime.strptime(start_date, "%Y.%m.%d")
    end_date = datetime.strptime(end_date, "%Y.%m.%d")
    
    mt5_timeframe = mt5.TIMEFRAME_H1
    
    rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'tick_volume']]
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df

cerebro = bt.Cerebro()
cerebro.broker.set_cash(1000000)  # 초기 자본을 1,000,000으로 설정

symbols = ['EURUSD', 'BITCOIN', '#USNDAQ100']
start_date = "2023.01.01"
end_date = "2023.10.22"

pip_values = {
    'EURUSD': 0.0001,
    'BITCOIN': 1,
    '#USNDAQ100': 1
}

for symbol in symbols:
    data = get_mt5_data(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
    feed = SymbolData(dataname=data, name=symbol, pip_value=pip_values[symbol])
    cerebro.adddata(feed)

# 전략을 cerebro에 직접 추가
cerebro.addstrategy(MovingAverageCrossStrategy)

print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
results = cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

# 첫 번째 전략 인스턴스 가져오기
strategy = results[0]

# 거래 내역 출력
print("\n거래 내역:")
for trade in strategy.trades:
    print(f"심볼: {trade['symbol']}, 크기: {trade['size']:.2f}, "
          f"진입가: {trade['entry_price']:.2f}, 청산가: {trade['exit_price']:.2f}, "
          f"가치: {trade['value']:.2f}, PNL: {trade['pnl']:.2f}, 순PNL: {trade['pnlcomm']:.2f}, "
          f"수수료: {trade['commission']:.2f}")

cerebro.plot()

mt5.shutdown()
