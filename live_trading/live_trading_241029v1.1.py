import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from live_feed import LiveFeed
import time

class Position:
    """단일 포지션 정보 관리"""
    def __init__(self):
        self.ticket = None        # MT5 티켓 번호
        self.type = None         # 'BUY' or 'SELL'
        self.volume = None       # 거래량
        self.entry_price = None  # 진입가
        self.exit_price = None   # 청산가
        self.sl_price = None     # 손절가
        self.entry_time = None   # 진입시간
        self.close_time = None   # 청산시간
        self.profit = None       # 수익
        self.entry_atr = None    # 진입시 ATR 값

class PositionManager:
    """전체 포지션 관리"""
    def __init__(self):
        self.active_positions = {}   # symbol: [Position]
        self.closed_positions = []   # [Position]
        self.total_units = 0        # 전체 유닛 수
        self.max_units = 15         # 최대 유닛 수
        self.max_units_per_symbol = 4  # 심볼당 최대 유닛

    def can_add_position(self, symbol):
        """새로운 포지션 추가 가능 여부 확"""
        if self.total_units >= self.max_units:
            return False
        
        symbol_positions = self.active_positions.get(symbol, [])
        if len(symbol_positions) >= self.max_units_per_symbol:
            return False
            
        return True

    def add_position(self, symbol, position):
        """포지션 추가"""
        if not self.can_add_position(symbol):
            return False
            
        if symbol not in self.active_positions:
            self.active_positions[symbol] = []
            
        self.active_positions[symbol].append(position)
        self.total_units += 1
        return True

    def close_position(self, symbol, ticket, exit_price, close_time):
        """포지션 청산"""
        if symbol not in self.active_positions:
            print(f"심볼 {symbol}에 대한 활성 포지션이 없습니다.")
            return False
            
        for i, pos in enumerate(self.active_positions[symbol]):
            if pos.ticket == ticket:
                pos.exit_price = exit_price
                pos.close_time = close_time
                pos.profit = (exit_price - pos.entry_price) if pos.type == 'BUY' else (pos.entry_price - exit_price)
                
                # 청산된 포지션 이동
                self.closed_positions.append(pos)
                self.active_positions[symbol].pop(i)
                self.total_units -= 1
                
                # 심볼의 모든 포지션이 청산되면 해당 심볼 제거
                if not self.active_positions[symbol]:
                    del self.active_positions[symbol]
                
                return True
                
        print(f"티켓 {ticket}에 해당하는 포지션을 찾을 수 없습니다.")
        return False

    def get_positions(self, symbol):
        """심볼의 활성 포지션 조회"""
        return self.active_positions.get(symbol, [])

    def update_sl(self, symbol, ticket, new_sl):
        """포지션 손절가 업데이트"""
        if symbol not in self.active_positions:
            print(f"심볼 {symbol}에 대한 활성 포지션이 없습니다.")
            return False
            
        for pos in self.active_positions[symbol]:
            if pos.ticket == ticket:
                pos.sl_price = new_sl
                return True
                
        print(f"티켓 {ticket}에 해당하는 포지션을 찾을 수 없습니다.")
        return False

class TechnicalAnalysis:
    """기술적 지표 계산"""
    def __init__(self):
        self.atr_period = 20     # ATR 기간
        self.ema_short = 5       # 단기 EMA
        self.ema_mid = 20        # 중기 EMA
        self.ema_long = 40       # 장기 EMA
        
    def calculate_indicators(self, df):
        """기술적 지표 계산"""
        # EMA 계산
        df['ema_short'] = ta.ema(df['close'], length=self.ema_short)
        df['ema_mid'] = ta.ema(df['close'], length=self.ema_mid)
        df['ema_long'] = ta.ema(df['close'], length=self.ema_long)
        
        # ATR 계산 (EMA 사용)
        df['atr'] = ta.atr(
            high=df['high'], 
            low=df['low'], 
            close=df['close'], 
            length=self.atr_period,
            mamode='ema'  # EMA 사용 설정
        )
        
        return df

    def generate_signal(self, df):
        """거래 신호 생성"""
        if len(df) < self.ema_long:
            return None
            
        df = self.calculate_indicators(df)
        current = df.iloc[-2]  # 완성된 마지막 봉
        
        # EMA 정배열/역배열 확인
        ema_bull = (current['ema_short'] > current['ema_mid'] > current['ema_long'])
        ema_bear = (current['ema_short'] < current['ema_mid'] < current['ema_long'])
        
        if ema_bull and self.additional_filters(df):
            return 'BUY'
        elif ema_bear and self.additional_filters(df):
            return 'SELL'
            
        return None

    def additional_filters(self, df):
        """추가 필터"""
        current = df.iloc[-2]
        
        # 거래량 필터 (real_volume 사용)
        volume_ma = df['real_volume'].rolling(20).mean()
        if current['real_volume'] < volume_ma.iloc[-2] * 0.5:
            return False
            
        # 변동성 필터
        atr_ma = df['atr'].rolling(20).mean()
        if current['atr'] > atr_ma.iloc[-2] * 2:
            return False
            
        return True

    def check_close_signal(self, df, symbol, position_type):
        """청산 신호 확인"""
        if len(df) < self.ema_long:
            return False
            
        df = self.calculate_indicators(df)
        current = df.iloc[-2]  # 완성된 마지막 봉
        
        # 롱 포지션 청산: EMA 정배열이 깨질 때
        if position_type == 'BUY':
            return not (current['ema_short'] > current['ema_mid'] > current['ema_long'])
            
        # 숏 포지션 청산: EMA 역배열이 깨질 때
        elif position_type == 'SELL':
            return not (current['ema_short'] < current['ema_mid'] < current['ema_long'])
            
        return False

class LiveTrading:
    """실시간 거래 시스템"""
    def __init__(self, symbols):
        """실시간 거래 초기화"""
        if not mt5.initialize():
            print("MT5 초기화 실패")
            return
            
        print("\n=== 시스템 초기화 ===")
        self.position_manager = PositionManager()
        self.technical_analysis = TechnicalAnalysis()
        self.symbols = symbols
        
        print("\n=== 실시간 데이터 피드 초기화 ===")
        self.feed = LiveFeed(symbols)
        
        # 기존 포지션 확인
        self.check_existing_positions()
        
    def check_existing_positions(self):
        """기존 포지션 확인"""
        print("\n=== 기존 포지션 확인 ===")
        for symbol in self.symbols:
            positions = mt5.positions_get(symbol=symbol)
            if positions:
                for pos in positions:
                    position = Position()
                    position.ticket = pos.ticket
                    position.type = 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                    position.volume = pos.volume
                    position.entry_price = pos.price_open
                    position.entry_time = datetime.utcfromtimestamp(pos.time)
                    position.profit = pos.profit
                    
                    # 포지 추가
                    self.position_manager.add_position(symbol, position)
                    
                    print(f"\n{symbol} 기존 포지션:")
                    print(f"티켓: {position.ticket}")
                    print(f"유형: {position.type}")
                    print(f"수량: {position.volume}")
                    print(f"진입가: {position.entry_price}")
                    print(f"진입시간: {position.entry_time}")
                    print(f"현재손익: {position.profit}")
            else:
                print(f"\n{symbol} 포지션 없음")

    def calculate_position_size(self, symbol, atr):
        """포지션 크기 계산 (1% 리스크 기준)"""
        # TODO: 실제 운영시에는 아래 코드로 실제 계좌 자산 사용
        # account_info = mt5.account_info()
        # if account_info is None:
        #     print(f"{symbol} 계좌 정보 조회 실패")
        #     return 0.01
        # account_value = account_info.equity
        
        # 테스트를 위해 100$ 고정 사용
        account_value = 100.0
            
        # 심볼 정보 확인
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"{symbol} 심볼 정보 없음")
            return 0.01
            
        # 달러 변동폭 계산
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        dollar_volatility = (atr / tick_size) * tick_value
        
        # 유닛 크기 계산 (1% 리스크)
        risk_amount = account_value * 0.01
        unit_size = risk_amount / dollar_volatility
        
        
        # 최소/최대 거래량 제한
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        step = symbol_info.volume_step
        
        # 거래량 조정
        position_size = max(min_lot, min(max_lot, round(unit_size / step) * step))
        
        print(f"\n{symbol} 포지션 크기 계산:")
        print(f"계좌 자산: {account_value}")
        print(f"리스크 금액: {risk_amount}")
        print(f"ATR: {atr}")
        print(f"틱 크기: {tick_size}")
        print(f"틱 가치: {tick_value}")
        print(f"달러 변동폭: {dollar_volatility}")
        print(f"계산된 거래량: {position_size}")
        
        return position_size

    def execute_trade(self, symbol, signal, atr):
        """거래 실행"""
        if not self.position_manager.can_add_position(symbol):
            print(f"{symbol} 추가 포지션 불가")
            return
            
        # 포지션 크기 계산
        volume = self.calculate_position_size(symbol, atr)
        
        # 주문 요청 생성
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
            "magic": 241029,
            "comment": "v1.1 entry",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # 손절가 계산
        symbol_info = mt5.symbol_info(symbol)
        if signal == 'BUY':
            new_sl = symbol_info.ask - (2 * atr)
        else:
            new_sl = symbol_info.bid + (2 * atr)
        
        request["sl"] = new_sl
        
        # 주문 실행
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"주문 실패: {result.comment}")
            return
            
        # 주문 후 포지션 정보 조회
        position_info = mt5.positions_get(ticket=result.order)[0]
        
        # 포지션 정보 생성
        position = Position()
        position.ticket = result.order
        position.type = signal
        position.volume = volume
        position.entry_price = result.price
        position.sl_price = new_sl
        position.entry_time = datetime.utcfromtimestamp(position_info.time)
        position.entry_atr = atr
        
        # 기존 포지션이 있는 경우 (피라미딩)
        existing_positions = self.position_manager.get_positions(symbol)
        if existing_positions:
            print(f"\n{symbol} 피라미딩: 기존 포지션 손절가 업데이트")
            # 기존 포지션들의 손절가 업데이트
            for pos in existing_positions:
                # MT5에 손절가 수정 요청
                modify_request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": symbol,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "magic": 241029
                }
                modify_result = mt5.order_send(modify_request)
                if modify_result.retcode != mt5.TRADE_RETCODE_DONE:
                    print(f"손절가 수정 실패 (티켓: {pos.ticket}): {modify_result.comment}")
                else:
                    # Position Manager에도 업데이트
                    self.position_manager.update_sl(symbol, pos.ticket, new_sl)
                    print(f"손가 수정 완료 (티켓: {pos.ticket}): {new_sl:.5f}")
        
        # 새 포지션 추가
        self.position_manager.add_position(symbol, position)
        print(f"{symbol} {signal} 주문 성공 (티켓: {position.ticket})")

    def check_pyramid_signal(self, symbol, position_type, current_price, entry_atr):
        """피라미딩 신호 확인"""
        positions = self.position_manager.get_positions(symbol)
        if not positions:
            return False
            
        # 마지막 진입 포지션 확인
        last_position = positions[-1]
        if last_position.type != position_type:
            return False
            
        # 1/2N 이상 움직였는지 확인
        half_n = 0.5 * entry_atr
        if position_type == 'BUY':
            return current_price > (last_position.entry_price + half_n)
        else:
            return current_price < (last_position.entry_price - half_n)

    def close_all_positions(self, symbol, reason=""):
        """심볼의 모든 포지션 청산"""
        positions = self.position_manager.get_positions(symbol)
        if not positions:
            return
            
        print(f"\n{symbol} 전체 포지션 청산 시작 ({reason})")
        
        # MT5의 실제 포지션 확인
        mt5_positions = mt5.positions_get(symbol=symbol)
        if not mt5_positions:
            print(f"{symbol}의 실제 포지션이 없습니다. Position Manager 정리")
            # Position Manager 정리
            for pos in positions:
                self.position_manager.close_position(
                    symbol,
                    pos.ticket,
                    pos.entry_price,  # 마지막 가격으로 대체
                    datetime.utcnow()
                )
            return
            
        # 심볼 정보 확인
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"{symbol} 심볼 정보 없음")
            return
            
        # MT5의 실제 포지션만 처리
        for mt5_pos in mt5_positions:
            # 현재 가격 확인
            if mt5_pos.type == mt5.POSITION_TYPE_BUY:
                price = symbol_info.bid
            else:
                price = symbol_info.ask
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": mt5_pos.volume,
                "type": mt5.ORDER_TYPE_SELL if mt5_pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": mt5_pos.ticket,
                "price": price,
                "deviation": 20,
                "magic": 241029,
                "comment": f"v1.1 close ({reason})",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"포지션 청산 실패 (티켓: {mt5_pos.ticket}): {result.comment}")
                continue
                
            # Position Manager 업데이트
            close_success = self.position_manager.close_position(
                symbol,
                mt5_pos.ticket,
                result.price,
                datetime.utcnow()
            )
            
            if close_success:
                print(f"{symbol} 포지션 청산 완료 (티켓: {mt5_pos.ticket})")
            else:
                print(f"{symbol} 포지션 정보 업데이트 실패 (티켓: {mt5_pos.ticket})")
        
        # 최종 상태 확인
        mt5_final_check = mt5.positions_get(symbol=symbol)
        remaining_positions = self.position_manager.get_positions(symbol)
        
        if not mt5_final_check and remaining_positions:
            print(f"{symbol}의 모든 실제 포지션이 청산됨. Position Manager 정리")
            # Position Manager 강제 정리
            for pos in remaining_positions:
                self.position_manager.close_position(
                    symbol,
                    pos.ticket,
                    pos.entry_price,  # 마지막 가격으로 대체
                    datetime.utcnow()
                )
        elif mt5_final_check:
            print(f"경고: {symbol}에 {len(mt5_final_check)}개의 실제 포지션이 남아있습니.")
        else:
            print(f"{symbol} 모든 포지션 청산 완료")

    def update_pyramid_stop_loss(self, symbol, new_sl):
        """피라미딩시 기존 포지션들의 손절가 업데이트"""
        positions = self.position_manager.get_positions(symbol)
        for position in positions:
            self.position_manager.update_sl(symbol, position.ticket, new_sl)

    def check_mt5_connection(self):
        """MT5 연결 상태 확인 및 재연결"""
        if not mt5.initialize():
            retry_count = 3
            while retry_count > 0:
                if mt5.initialize():
                    return True
                time.sleep(1)
                retry_count -= 1
            return False
        return True

    def sync_positions(self):
        """MT5 실제 포지션과 Position Manager 동기화"""
        for symbol in self.symbols:
            # Position Manager의 포지션 목록
            managed_positions = self.position_manager.get_positions(symbol)
            if not managed_positions:
                continue
                
            # MT5의 실제 포지션 목록
            mt5_positions = mt5.positions_get(symbol=symbol)
            mt5_tickets = set() if mt5_positions is None else {pos.ticket for pos in mt5_positions}
            
            # Position Manager에는 있지만 MT5에는 없는 포지션 처리 (청산된 포지션)
            for pos in managed_positions:
                if pos.ticket not in mt5_tickets:
                    # 청산된 포지션의 최종 정보 조회
                    history_deals = mt5.history_deals_get(
                        ticket=pos.ticket,
                        position=pos.ticket
                    )
                    if history_deals:
                        # 청산 정보로 포지션 업데이트
                        close_deal = history_deals[-1]  # 마지막 거래가 청산 거래
                        self.position_manager.close_position(
                            symbol,
                            pos.ticket,
                            close_deal.price,
                            datetime.utcfromtimestamp(close_deal.time)
                        )
                        print(f"\n{symbol} 포지션 자동 청산 감지 (티켓: {pos.ticket})")
                        print(f"청산가: {close_deal.price:.5f}")
                        print(f"청산시간: {datetime.utcfromtimestamp(close_deal.time)}")
                    else:
                        # 히스토리를 찾을 수 없는 경우
                        print(f"\n{symbol} 포지션 청산 감지 (티켓: {pos.ticket})")
                        # 마지막 알려진 가격으로 청산 처리
                        self.position_manager.close_position(
                            symbol,
                            pos.ticket,
                            pos.entry_price,
                            datetime.utcnow()
                        )

    def run(self):
        """실시간 거래 실행"""
        try:
            last_update_time = None
            while True:
                self.feed.wait_for_next_minute()  # 다음 분의 정각까지 대기
                
                # 현재 시간 확인 (분 단위까지만)
                current_time = mt5.symbol_info_tick(self.symbols[0]).time
                current_time_minute = datetime.utcfromtimestamp(current_time).replace(second=0, microsecond=0)
                
                # 같은 분에 대해 중복 업데이트 방지
                if current_time_minute == last_update_time:
                    time.sleep(0.1)  # 짧은 대기 후 다시 시도
                    continue
                    
                self.feed.update()  # 데이터 업데이트
                
                # 포지션 동기화 전에 MT5 연결 상태 확인
                if not self.check_mt5_connection():
                    print("MT5 연결 실패")
                    continue
                
                self.sync_positions()  # 포지션 동기화
                
                # 각 심볼에 대해 신호 생성 및 거래 실행
                for symbol in self.symbols:
                    df = self.feed.get_data(symbol)
                    if df is None or len(df) < self.technical_analysis.ema_long:
                        continue
                        
                    # 기술적 지표 계산
                    df = self.technical_analysis.calculate_indicators(df)
                    
                    # 마지막 두 봉의 정보 출력
                    if len(df) >= 2:
                        print(f"\n{symbol} 완성된 마지막 두 봉 정보:")
                        print(f"[-2] [{df.index[-2]}] "
                              f"시가: {df['open'][-2]:.5f}, "
                              f"고가: {df['high'][-2]:.5f}, "
                              f"저가: {df['low'][-2]:.5f}, "
                              f"종가: {df['close'][-2]:.5f}, "
                              f"볼륨: {df['tick_volume'][-2]}")
                        print(f"[-1] [{df.index[-1]}] "
                              f"시가: {df['open'][-1]:.5f}, "
                              f"고가: {df['high'][-1]:.5f}, "
                              f"저가: {df['low'][-1]:.5f}, "
                              f"종가: {df['close'][-1]:.5f}, "
                              f"볼륨: {df['tick_volume'][-1]}")
                    
                    # MT5에서 직접 포지션 정보 확인
                    mt5_positions = mt5.positions_get(symbol=symbol)
                    if mt5_positions:
                        total_profit = 0
                        symbol_info = mt5.symbol_info(symbol)
                        point_value = symbol_info.point
                        tick_value = symbol_info.trade_tick_value
                        positions_count = len(mt5_positions)
                        
                        for mt5_pos in mt5_positions:
                            current_price = df['close'][-1]
                            profit = (current_price - mt5_pos.price_open) if mt5_pos.type == mt5.POSITION_TYPE_BUY else (mt5_pos.price_open - current_price)
                            profit *= mt5_pos.volume * tick_value / point_value
                            total_profit += profit
                        
                        print(f"\n{symbol} 포지션: {positions_count} 유닛 (손익: {total_profit:.2f}$)")
                        for mt5_pos in mt5_positions:
                            pos_type = 'BUY' if mt5_pos.type == mt5.POSITION_TYPE_BUY else 'SELL'
                            profit = (current_price - mt5_pos.price_open) if mt5_pos.type == mt5.POSITION_TYPE_BUY else (mt5_pos.price_open - current_price)
                            profit *= mt5_pos.volume * tick_value / point_value
                            print(f"┗ 타입: {pos_type}, 볼륨: {mt5_pos.volume:.2f}, "
                                  f"진입가: {mt5_pos.price_open:.5f}, 손절가: {mt5_pos.sl:.5f}, "
                                  f"손익: {profit:.2f}$")
                        
                        # EMA 상태 출력
                        current = df.iloc[-1]
                        ema_status = (
                            f"EMA 상태: {current['ema_short']:.5f} / {current['ema_mid']:.5f} / {current['ema_long']:.5f}"
                        )
                        pos_type = 'BUY' if mt5_positions[0].type == mt5.POSITION_TYPE_BUY else 'SELL'
                        if pos_type == 'BUY':
                            is_aligned = current['ema_short'] > current['ema_mid'] > current['ema_long']
                            print(f"┗ 롱 포지션 {ema_status} (정배열: {'유지중' if is_aligned else '깨짐'})")
                        else:
                            is_aligned = current['ema_short'] < current['ema_mid'] < current['ema_long']
                            print(f"┗ 숏 포지션 {ema_status} (역배열: {'유지중' if is_aligned else '깨짐'})")
                    
                    current = df.iloc[-1]  # 완성된 마지막 봉
                    current_atr = current['atr']
                    
                    # 청산 신호 확인
                    if mt5_positions:
                        position_type = mt5_positions[0].type
                        if self.technical_analysis.check_close_signal(df, symbol, position_type):
                            self.close_all_positions(symbol, "전략 청산")
                            continue
                    
                    # 신규 진입 또는 피라미딩
                    signal = self.technical_analysis.generate_signal(df)
                    if signal:
                        if not mt5_positions:
                            # 신규 진입
                            print(f"{symbol} 신규 진입 신호: {signal}")
                            self.execute_trade(symbol, signal, current_atr)
                        elif mt5_positions[0].type == signal:
                            # 피라미딩 확인
                            symbol_info = mt5.symbol_info(symbol)
                            current_price = symbol_info.ask if signal == 'BUY' else symbol_info.bid
                            
                            if self.check_pyramid_signal(symbol, signal, current_price, current_atr):
                                print(f"{symbol} 피라미딩 신호: {signal}")
                                self.execute_trade(symbol, signal, current_atr)
                
                last_update_time = current_time_minute
                
        except KeyboardInterrupt:
            print("\n프로그램 종료")
        finally:
            mt5.shutdown()

    def save_position_history(self):
        """포지션 정보 저장"""
        history_data = {
            'active_positions': self.position_manager.active_positions,
            'closed_positions': self.position_manager.closed_positions
        }
        # JSON 형식으로 저장

def main():
    """메인 함수"""
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return
        
    # 거래 가능한 심볼 선택 (예: 상위 10개)
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