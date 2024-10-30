from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def get_mt5_data(symbol, timeframe, start_date, end_date):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    rates = mt5.copy_rates_range(symbol, timeframe, start_timestamp, end_timestamp)
    mt5.shutdown()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    })
    
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

class SMACrossOver(Strategy):
    n1 = 10  # 단기 이동평균 기간
    n2 = 30  # 장기 이동평균 기간

    def init(self):
        self.sma1 = self.I(lambda: self.data.Close.rolling(self.n1).mean())
        self.sma2 = self.I(lambda: self.data.Close.rolling(self.n2).mean())

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.sell()

def run_backtest(symbol, timeframe, start_date, end_date):
    df = get_mt5_data(symbol, timeframe, start_date, end_date)
    if df is None or df.empty:
        print("데이터를 가져오는 데 실패했습니다.")
        return

    print(f"데이터 샘플:\n{df.head()}\n")
    print(f"데이터 통계:\n{df.describe()}\n")
    print(f"총 데이터 수: {len(df)}")

    bt = Backtest(df, SMACrossOver, cash=10000, commission=.002)
    stats = bt.run()
    print(stats)

    bt.plot()

if __name__ == "__main__":
    symbol = "EURUSD"
    timeframe = mt5.TIMEFRAME_H1
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 12, 31)

    run_backtest(symbol, timeframe, start_date, end_date)
