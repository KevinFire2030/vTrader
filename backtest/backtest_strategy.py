from base_strategy import BaseStrategy

class BacktestStrategy(BaseStrategy):
    """백테스팅용 전략 클래스"""
    
    def on_trade_closed(self, trade_info):
        """거래 종료 시 호출되는 메서드"""
        print(f'\n거래 종료 (백테스트):')
        print(f'심볼: {trade_info["Symbol"]}')
        print(f'날짜: {trade_info["Date"]}')
        print(f'유형: {trade_info["Type"]}')
        print(f'가격: {trade_info["Price"]:.5f}')
        print(f'수량: {trade_info["Size"]}')
        print(f'수수료: {trade_info["Commission"]:.5f}')
        print(f'손익: {trade_info["PnL"]:.2f}')
    
    def on_order_completed(self, order):
        """주문 체결 시 호출되는 메서드"""
        print(f'주문 체결 (백테스트):')
        print(f'심볼: {order.data._name}')
        print(f'유형: {"매수" if order.isbuy() else "매도"}')
        print(f'가격: {order.executed.price:.5f}')
        print(f'수량: {order.executed.size}')
    
    def on_order_failed(self, order):
        """주문 실패 시 호출되는 메서드"""
        print(f'주문 실패 (백테스트):')
        print(f'심볼: {order.data._name}')
        print(f'상태: {order.status}')
