import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import pytz

def get_symbol_info(symbol):
    if not mt5.initialize():
        print("MT5 초기화 실패")
        return None

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"심볼 {symbol}에 대한 정보를 가져올 수 없습니다.")
        mt5.shutdown()
        return None

    # 심볼 정보를 딕셔너리로 변환
    info_dict = symbol_info._asdict()

    # 각 속성에 대한 설명
    descriptions = {
        'custom': '사용자 정의 심볼 여부',
        'chart_mode': '가격 차트 유형',
        'select': '마켓워치에서 선택된 심볼 여부',
        'visible': '마켓워치에서 표시된 심볼 여부',
        'session_deals': '현재 세션의 거래 수',
        'session_buy_orders': '현재 매수 주문 수',
        'session_sell_orders': '현재 매도 주문 수',
        'volume': '최근 거래량',
        'volumehigh': '최대 거래량',
        'volumelow': '최소 거래량',
        'time': '최근 시세 시간',
        'digits': '소수점 이��� 자릿수',
        'spread': '스프레드 값',
        'spread_float': '변동 스프레드 여부',
        'ticks_bookdepth': '요청된 틱의 최대 수',
        'trade_calc_mode': '계약 비용 계산 모드',
        'trade_mode': '주문 실행 유형',
        'start_time': '심볼 거래 시작 날짜',
        'expiration_time': '심볼 거래 종료 날짜',
        'trade_stops_level': '최소 중지 수준(틱)',
        'trade_freeze_level': '거래 동결 수준',
        'trade_exemode': '거래 실행 모드',
        'swap_mode': '스왑 계산 모드',
        'swap_rollover3days': '3일 스왑 롤오버 일',
        'margin_hedged_use_leg': '헤지 마진 계산 모드',
        'expiration_mode': '주문 만료 모드 플래그',
        'filling_mode': '주문 채우기 모드 플래그',
        'order_mode': '허용된 주문 유형 플래그',
        'order_gtc_mode': 'GTC 주문의 만료 기간',
        'option_mode': '옵션 유형',
        'option_right': '옵션 권리',
        'bid': '현재 매수 가격',
        'bidhigh': '현재 기간의 최고 매수 가격',
        'bidlow': '현재 기간의 최저 매수 가격',
        'ask': '현재 매도 가격',
        'askhigh': '현재 기간의 최고 매도 가격',
        'asklow': '현재 기간의 최저 매도 가격',
        'last': '최근 거래 가격',
        'lasthigh': '현재 기간의 최고 거래 가격',
        'lastlow': '현재 기간의 최저 거래 가격',
        'volume_real': '거래량',
        'volumehigh_real': '최대 거래량',
        'volumelow_real': '최소 거래량',
        'option_strike': '옵션 행사 가격',
        'point': '심볼 포인트 값',
        'trade_tick_value': '계약 가치 변화 값',
        'trade_tick_value_profit': '이익 계산을 위한 틱 가치',
        'trade_tick_value_loss': '손실 계산을 위한 틱 가치',
        'trade_tick_size': '최소 가격 변화',
        'trade_contract_size': '거래 계약 크기',
        'trade_accrued_interest': '누적 이자',
        'trade_face_value': '채권의 액면가',
        'trade_liquidity_rate': '유동성 비율',
        'volume_min': '최소 거래량',
        'volume_max': '최대 거래량',
        'volume_step': '최소 거래량 변화 단계',
        'volume_limit': '허용된 최대 총 거래량',
        'swap_long': '롱 포지션 스왑 값',
        'swap_short': '숏 포지션 스왑 값',
        'margin_initial': '초기 마진 요구사항',
        'margin_maintenance': '유지 마진 요구사항',
        'session_volume': '현재 세션 거래량 합계',
        'session_turnover': '현재 세션 거래 회전율 합계',
        'session_interest': '현재 세션 미결제약정 합계',
        'session_buy_orders_volume': '현재 매수 주 거래량',
        'session_sell_orders_volume': '현재 매도 주문 거래량',
        'session_open': '현재 세션 시가',
        'session_close': '현재 세션 종가',
        'session_aw': '현재 세션 평균 가중 가격',
        'session_price_settlement': '현재 세션 정산 가격',
        'session_price_limit_min': '현재 세션 최소 가격',
        'session_price_limit_max': '현재 세션 최대 가격',
        'margin_hedged': '헤지된 포지션에 대한 계약 크기 또는 마진',
        'price_change': '마지막 거래일 이후 가격 변화',
        'price_volatility': '가격 변동성',
        'price_theoretical': '옵션의 이론 가격',
        'price_greeks_delta': '옵션의 델타 값',
        'price_greeks_theta': '옵션의 세타 값',
        'price_greeks_gamma': '옵션의 감마 값',
        'price_greeks_vega': '옵션의 베가 값',
        'price_greeks_rho': '옵션의 로 값',
        'price_greeks_omega': '옵션의 오메가 값',
        'price_sensitivity': '옵션의 가격 민감도',
        'basis': '선물 계약의 기초 자산',
        'category': '심볼의 카테고리',
        'currency_base': '기준 통화',
        'currency_profit': '수익 통화',
        'currency_margin': '마진 통화',
        'bank': '피드의 현재 데이터 소스',
        'description': '심볼 설명',
        'exchange': '심볼이 거래되는 거래소 이름',
        'formula': '사용자 정의 심볼 가격 공식',
        'isin': '심볼의 ISIN',
        'name': '심볼 이름',
        'page': '심볼 정보가 있는 웹 페이지 주소',
        'path': '심볼 트리 경로'
    }

    # 결과를 DataFrame으로 변환
    df = pd.DataFrame(list(info_dict.items()), columns=['Attribute', 'Value'])
    df['Description'] = df['Attribute'].map(descriptions)

    mt5.shutdown()
    return df

def unix_to_multiple_timezones(unix_timestamp):
    utc_time = datetime.utcfromtimestamp(unix_timestamp)
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    
    ny_tz = pytz.timezone('America/New_York')
    moscow_tz = pytz.timezone('Europe/Moscow')
    seoul_tz = pytz.timezone('Asia/Seoul')
    
    ny_time = utc_time.astimezone(ny_tz)
    moscow_time = utc_time.astimezone(moscow_tz)
    seoul_time = utc_time.astimezone(seoul_tz)
    
    return {
        'NY': ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Moscow': moscow_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'Seoul': seoul_time.strftime('%Y-%m-%d %H:%M:%S %Z')
    }

def print_symbol_info(symbol):
    df = get_symbol_info(symbol)
    if df is not None:
        print(f"{symbol} 심볼 정보:")
        for _, row in df.iterrows():
            if row['Attribute'] in ['time', 'start_time', 'expiration_time']:
                times = unix_to_multiple_timezones(row['Value'])
                print(f"{row['Attribute']}:")
                print(f"  값: {row['Value']}")
                print(f"  (뉴욕 : {times['NY']})")
                print(f"  (모스크바: {times['Moscow']})")
                print(f"  (서울: {times['Seoul']})")
                print(f"  설명: {row['Description']}")
            else:
                print(f"{row['Attribute']}:")
                print(f"  값: {row['Value']}")
                print(f"  설명: {row['Description']}")
            print()

if __name__ == "__main__":
    symbol = input("심볼을 입력하세요: ")
    print_symbol_info(symbol)
