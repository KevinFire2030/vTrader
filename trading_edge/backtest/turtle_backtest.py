import datetime
import backtrader as bt
import mt5
import pandas as pd

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
