class PyramidOrder:
    """피라미딩 주문 정보"""
    def __init__(self):
        self.ticket = None        # MT5 주문 티켓
        self.type = None         # 'BUY' or 'SELL'
        self.volume = None       # 거래량
        self.price = None        # 주문 가격
        self.sl = None          # 손절가
        self.parent_ticket = None # 원래 포지션의 티켓

class PyramidManager:
    """피라미딩 주문 관리"""
    def __init__(self):
        self.pending_orders = {}  # symbol: [PyramidOrder]
        self.max_pyramids = 4    # 최대 피라미딩 수
    
    def place_orders(self, symbol, position, atr):
        """피라미딩 주문 설정"""
        pyramid_prices = []
        is_buy = position.type == 'BUY'
        half_n = 0.5 * atr
        
        # 피라미딩 가격 계산
        for i in range(1, self.max_pyramids + 1):
            price = (position.entry_price + (half_n * i)) if is_buy else (position.entry_price - (half_n * i))
            pyramid_prices.append(price)
        
        # 피라미딩 주문 설정
        orders = []
        for i, price in enumerate(pyramid_prices, 1):
            # MT5 주문 요청
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": position.volume,  # 동일한 크기로 설정
                "type": mt5.ORDER_TYPE_BUY_STOP if is_buy else mt5.ORDER_TYPE_SELL_STOP,
                "price": price,
                "sl": price + (2 * atr) if not is_buy else price - (2 * atr),
                "magic": 241030,
                "comment": f"v1.0 pyramid #{i}",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                order = PyramidOrder()
                order.ticket = result.order
                order.type = position.type
                order.volume = position.volume
                order.price = price
                order.sl = request["sl"]
                order.parent_ticket = position.ticket
                orders.append(order)
                print(f"피라미딩 주문 #{i} 설정 완료 (티켓: {order.ticket})")
            else:
                print(f"피라미딩 주문 #{i} 설정 실패: {result.comment}")
        
        if orders:
            self.pending_orders[symbol] = orders
            return True
        return False
    
    def cancel_orders(self, symbol):
        """심볼의 모든 피라미딩 주문 취소"""
        if symbol not in self.pending_orders:
            return
            
        for order in self.pending_orders[symbol]:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
                "magic": 241030
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"피라미딩 주문 취소 완료 (티켓: {order.ticket})")
            else:
                print(f"피라미딩 주문 취소 실패 (티켓: {order.ticket}): {result.comment}")
        
        del self.pending_orders[symbol]
    
    def get_orders(self, symbol):
        """심볼의 피라미딩 주문 조회"""
        return self.pending_orders.get(symbol, [])
    
    def check_execution(self, symbol):
        """체결된 피라미딩 주문 확인"""
        if symbol not in self.pending_orders:
            return
            
        # MT5에서 실제 주문 상태 확인
        orders = mt5.orders_get(symbol=symbol)
        if orders is None:
            orders = []
            
        current_tickets = {order.ticket for order in orders}
        executed_orders = []
        
        # 체결된 주문 찾기
        for order in self.pending_orders[symbol]:
            if order.ticket not in current_tickets:
                executed_orders.append(order)
        
        # 체결된 주문 제거
        if executed_orders:
            self.pending_orders[symbol] = [
                order for order in self.pending_orders[symbol]
                if order not in executed_orders
            ]
            
        return executed_orders 