import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
from live_feed import LiveFeed

class TradingStrategy:
    def __init__(self):
        """거래 전략 초기화"""
        self.positions = {}  # 각 심볼의 포지션 상태
    
    def generate_signal(self, df, symbol):
        """거래 신호 생성 (완성된 마지막 봉 기준)"""
        if len(df) < 3:  # 최소 3개의 봉이 필요
            return None
            
        # 완성된 마지막 봉 [-2]와 그 이전 봉 [-3] 사용
        current_bar = df.iloc[-2]
        prev_bar = df.iloc[-3]
        
        # 단순한 상승/하락 판단
        if current_bar['close'] > prev_bar['close']:
            return 'BUY'
        elif current_bar['close'] < prev_bar['close']:
            return 'SELL'
        
        return None

    def check_positions(self, symbols):
        """현재 포지션 확인"""
        for symbol in symbols:
            positions = mt5.positions_get(symbol=symbol)
            
            if positions:
                # 심볼의 모든 포지션 정보 저장
                self.positions[symbol] = []
                for position in positions:
                    pos_info = {
                        'ticket': position.ticket,
                        'type': 'BUY' if position.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        'volume': position.volume,
                        'price': position.price_open,
                        'time': position.time,
                        'profit': position.profit
                    }
                    self.positions[symbol].append(pos_info)
                    
                print(f"\n{symbol} 기존 포지션 발견:")
                for pos in self.positions[symbol]:
                    print(f"티켓: {pos['ticket']}")
                    print(f"유형: {pos['type']}")
                    print(f"수량: {pos['volume']}")
                    print(f"진입가: {pos['price']}")
                    print(f"포지션 시간: {datetime.fromtimestamp(pos['time'])}")
                    print(f"현재 손익: {pos['profit']}")
            else:
                self.positions[symbol] = []
                print(f"\n{symbol} 포지션 없음")

class LiveTrading:
    def __init__(self, symbols):
        """실시간 거래 초기화"""
        if not mt5.initialize():
            print("MT5 초기화 실패")
            return
            
        print("\n=== 기존 포지션 확인 ===")
        self.strategy = TradingStrategy()
        self.strategy.check_positions(symbols)
        
        print("\n=== 실시간 데이터 피드 초기화 ===")
        self.feed = LiveFeed(symbols)
        
    def close_position(self, symbol, position):
        """포지션 종료"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": position['volume'],
            "type": mt5.ORDER_TYPE_BUY if position['type'] == 'SELL' else mt5.ORDER_TYPE_SELL,
            "position": position['ticket'],
            "magic": 241028,
            "comment": "python script close",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"포지션 종료 실패: {result.comment}")
            return False
        else:
            print(f"포지션 종료 성공: {symbol} ({position['type']} 청산)")
            return True

    def execute_trade(self, symbol, signal):
        """거래 실행"""
        # 현재 포지션 확인
        current_positions = self.strategy.positions.get(symbol, [])
        
        if signal == 'BUY':
            # 매도 포지션이 있으면 먼저 청산
            sell_positions = [p for p in current_positions if p['type'] == 'SELL']
            for pos in sell_positions:
                if self.close_position(symbol, pos):
                    print(f"{symbol} 매도 포지션 청산 후 매수 시도")
                else:
                    print(f"{symbol} 매도 포지션 청산 실패")
                    return
            
            # 매수 포지션이 있는지 확인
            buy_positions = [p for p in current_positions if p['type'] == 'BUY']
            if buy_positions:
                print(f"{symbol} 이미 매수 포지션 있음")
                return
                
            # 매수 주문
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_BUY,
                "magic": 241028,
                "comment": "python script open",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"매수 주문 실패: {result.comment}")
            else:
                print(f"매수 주문 성공: {symbol}")
                # 포지션 정보 업데이트
                self.strategy.check_positions([symbol])
                
        elif signal == 'SELL':
            # 매수 포지션이 있으면 먼저 청산
            buy_positions = [p for p in current_positions if p['type'] == 'BUY']
            for pos in buy_positions:
                if self.close_position(symbol, pos):
                    print(f"{symbol} 매수 포지션 청산 후 매도 시도")
                else:
                    print(f"{symbol} 매수 포지션 청산 실패")
                    return
            
            # 매도 포지션이 있는지 확인
            sell_positions = [p for p in current_positions if p['type'] == 'SELL']
            if sell_positions:
                print(f"{symbol} 이미 매도 포지션 있음")
                return
                
            # 매도 주문
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_SELL,
                "magic": 241028,
                "comment": "python script open",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"매도 주문 실패: {result.comment}")
            else:
                print(f"매도 주문 성공: {symbol}")
                # 포지션 정보 업데이트
                self.strategy.check_positions([symbol])
    
    def run(self):
        """실시간 거래 실행"""
        try:
            while True:
                self.feed.wait_for_next_minute()  # 다음 분의 정각까지 대기
                
                # 각 심볼에 대해 신호 생성 및 거래 실행
                for symbol in self.feed.symbols:
                    df = self.feed.get_data(symbol)
                    if df is not None:
                        signal = self.strategy.generate_signal(df, symbol)
                        if signal:
                            print(f"\n{symbol} 거래 신호: {signal}")
                            self.execute_trade(symbol, signal)
                
                self.feed.update()  # 데이터 업데이트
                
        except KeyboardInterrupt:
            print("\n프로그램 종료")
        finally:
            mt5.shutdown()

def main():
    """테스트 실행"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return
        
    symbols = []
    for symbol in mt5.symbols_get():
        if symbol.visible and len(symbols) < 10:
            symbols.append(symbol.name)
    
    if not symbols:
        print("심볼을 찾을 수 없습니다.")
        mt5.shutdown()
        return
    
    # 실시간 거래 시작
    trading = LiveTrading(symbols)
    trading.run()

if __name__ == '__main__':
    main()
