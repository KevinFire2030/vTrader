from backtrader import Strategy

class BaseStrategy(Strategy):
    """기본 전략 클래스 - 백테스팅과 라이브 트레이딩에서 공통으로 사용할 기능"""
    params = (
        ('stake', 0.01),  # 기본 거래 단위
    )
    
    def __init__(self):
        self.orders = {}  # 각 데이터피드별 주문 추적
        self.trades = []  # 거래 내역 저장
        
        # 각 데이터피드별로 종가 저장
        self.dataclose = {}
        for data in self.datas:
            self.dataclose[data._name] = data.close
    
    def notify_trade(self, trade):
        """거래 알림 처리"""
        if trade.isclosed:
            trade_info = {
                'Date': self.data.datetime.datetime(0),
                'Symbol': trade.data._name,
                'Type': 'Buy' if trade.size > 0 else 'Sell',
                'Price': trade.price,
                'Size': abs(trade.size),
                'Value': abs(trade.value),
                'Commission': trade.commission,
                'PnL': trade.pnl
            }
            self.trades.append(trade_info)
            self.on_trade_closed(trade_info)
    
    def notify_order(self, order):
        """주문 상태 알림 처리"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status == order.Completed:
            self.on_order_completed(order)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.on_order_failed(order)
    
    def on_trade_closed(self, trade_info):
        """거래 종료 시 호출되는 메서드"""
        pass
    
    def on_order_completed(self, order):
        """주문 체결 시 호출되는 메서드"""
        pass
    
    def on_order_failed(self, order):
        """주문 실패 시 호출되는 메서드"""
        pass
