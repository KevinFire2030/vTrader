from base_strategy import BaseStrategy
import MetaTrader5 as mt5
from datetime import datetime
import pytz

class LiveStrategy(BaseStrategy):
    """라이브 트레이딩용 전략 클래스"""
    
    def __init__(self):
        super().__init__()
        self.initialize_mt5()
    
    def initialize_mt5(self):
        """MT5 초기화"""
        if not mt5.initialize():
            print("MT5 초기화 실패")
            return False
        print("MT5 초기화 성공")
        return True
    
    def place_market_order(self, symbol, order_type, volume, price=None, comment=""):
        """MT5에 실제 주문을 전송하는 메서드"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "magic": 241028,  # 매직 넘버 설정
            "comment": comment,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if price:
            request["price"] = price
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"주문 실패: {result.comment}")
            return False
        return True
    
    def on_trade_closed(self, trade_info):
        """거래 종료 시 호출되는 메서드"""
        print(f'\n거래 종료 (라이브):')
        print(f'심볼: {trade_info["Symbol"]}')
        print(f'날짜: {trade_info["Date"]}')
        print(f'유형: {trade_info["Type"]}')
        print(f'가격: {trade_info["Price"]:.5f}')
        print(f'수량: {trade_info["Size"]}')
        print(f'수수료: {trade_info["Commission"]:.5f}')
        print(f'손익: {trade_info["PnL"]:.2f}')
        
        # 텔레그램 알림 등 추가 가능
    
    def on_order_completed(self, order):
        """주문 체결 시 호출되는 메서드"""
        symbol = order.data._name
        order_type = mt5.ORDER_TYPE_BUY if order.isbuy() else mt5.ORDER_TYPE_SELL
        volume = abs(order.size)
        price = order.executed.price
        
        # MT5에 실제 주문 전송
        success = self.place_market_order(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            price=price,
            comment=f"Backtrader Live Order"
        )
        
        if success:
            print(f'주문 체결 (라이브):')
            print(f'심볼: {symbol}')
            print(f'유형: {"매수" if order.isbuy() else "매도"}')
            print(f'가격: {price:.5f}')
            print(f'수량: {volume}')
        
    def on_order_failed(self, order):
        """주문 실패 시 호출되는 메서드"""
        print(f'주문 실패 (라이브):')
        print(f'심볼: {order.data._name}')
        print(f'상태: {order.status}')
        
        # 에러 로깅 및 알림 처리
        self.log_error(order)
    
    def log_error(self, order):
        """에러 로깅"""
        error_info = {
            'timestamp': datetime.now(pytz.UTC),
            'symbol': order.data._name,
            'type': "Buy" if order.isbuy() else "Sell",
            'status': order.status,
            'size': order.size,
            'price': order.created.price if order.created else None
        }
        # 여기에 에러 로깅 로직 추가
        print(f"에러 발생: {error_info}")
    
    def __del__(self):
        """소멸자: MT5 연결 종료"""
        mt5.shutdown()
