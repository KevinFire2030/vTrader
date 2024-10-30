import backtrader as bt
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz

class TurtleStrategy(bt.Strategy):
    params = (
        ('ema_fast', 5),
        ('ema_medium', 20),
        ('ema_slow', 40),
        ('atr_period', 14),
        ('risk_percent', 1.0),
    )

    def __init__(self):
        self.ema_fast = bt.indicators.EMA(period=self.params.ema_fast)
        self.ema_medium = bt.indicators.EMA(period=self.params.ema_medium)
        self.ema_slow = bt.indicators.EMA(period=self.params.ema_slow)
        self.atr = bt.indicators.ATR(period=self.params.atr_period)

    def next(self):
        if not self.position:
            if self.ema_fast > self.ema_medium > self.ema_slow:
                self.buy()
            elif self.ema_fast < self.ema_medium < self.ema_slow:
                self.sell()
        else:
            if self.position.size > 0:
                if self.ema_fast < self.ema_medium:
                    self.close()
            else:
                if self.ema_fast > self.ema_medium:
                    self.close()

def get_mt5_data(symbol, timeframe, start_date, end_date):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    timezone = pytz.timezone("Etc/UTC")
    utc_from = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone)
    utc_to = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone)

    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    mt5.shutdown()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

if __name__ == '__main__':
    symbol = "EURUSD"
    timeframe = mt5.TIMEFRAME_M15
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)

    data = get_mt5_data(symbol, timeframe, start_date, end_date)

    if data is not None:
        cerebro = bt.Cerebro()

        feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(feed)

        cerebro.addstrategy(TurtleStrategy)

        cerebro.broker.setcash(10000.0)
        cerebro.broker.setcommission(commission=0.001)  # 0.1% 수수료

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        cerebro.run()

        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        cerebro.plot()
    else:
        print("데이터를 가져오는데 실패했습니다.")
