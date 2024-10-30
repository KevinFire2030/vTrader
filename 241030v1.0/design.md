# vTrader v1.0 설계 문서

## 1. 시스템 개요

### 1.1 목적
- 터틀 트레이딩 기반의 자동 매매 시스템 구현
- 일평균 100$ 투자하여 1$ 수익 목표 (TE > 0)
- 안정적이고 신뢰할 수 있는 시스템 구축

### 1.2 거래 전략
0. 서버 전략
   - 시간 동기화
     * MT5 서버 시간 기준 동작
     * 매분 정각(00초)에 업데이트
     * 시간 동기화 상태 지속적 모니터링
   
   - 데이터 관리
     * 60개의 완성된 1분봉 유지
     * 미완성 봉 제외
     * 데이터 무결성 검증
   
   - MT5 연결 관리
     * 연결 상태 실시간 확인
     * 연결 끊김 시 자동 재연결
     * 재연결 실패시 안전 모드 전환

1. 진입 전략
   - EMA(5,20,40) 정배열/역배열 확인
   - 정배열: 롱 포지션 진입
   - 역배열: 숏 포지션 진입
   - 추가 필터: 거래량, 변동성 확인

2. 피라미딩 전략
   - 신규 진입 후 자동 피라미딩 주문 설정
     * 역지정가 주문으로 4개의 피라미딩 주문 동시 설정
     * 주문#1: 진입가 ± 1/2N
     * 주문#2: 진입가 ± 1/2N*2
     * 주문#3: 진입가 ± 1/2N*3
     * 주문#4: 진입가 ± 1/2N*4
   - 각 피라미딩 주문의 손절가: 주문가 ± 2ATR
   - 가격이 예상대로 움직이면 자동으로 피라미딩 진입
   - 반대 방향 움직임시 청산할 때 미체결 주문 자동 취소
   - 심볼당 최대 4유닛 제한 유지

3. 자금 관리 전략
   - 리스크 관리
     * 1유닛 = 계좌의 1% 리스크
     * 최대 리스크 = 계좌의 30% (15유닛)
     * 심볼당 최대 리스크 = 계좌의 8% (4유닛)
   
   - 포지션 크기 계산
     * 리스크 금액 = 계좌 자산 * 0.01 (1%)
     * 달러 변동폭 = ATR * (틱가치/틱크기)
     * 포지션 크기 = 리스크 금액 / 달러 변동폭
     * 최소/최대 거래량 제한 적용
   
   - 손절 관리
     * 진입시 손절폭 = 2ATR
     * 피라미딩시 손절가 재조정
     * 모든 포지션 동시 청산

4. 청산 전략
   - EMA 정배열/역배열 깨짐
   - 손절가 도달
   - 전체 포지션 동시 청산

## 2. 시스템 구조

### 1.1 핵심 모듈
1. TimeSync (시간 동기화)
   - 서버 시간 모니터링
   - 정각(00초) 대기
   - 시간 동기화 상태 확인

2. DataFeed (데이터 관리)
   - 60개의 완성된 봉 유지
   - 실시간 데이터 업데이트
   - 데이터 무결성 검증

3. Position (포지션 관리)
   - MT5 포지션 직접 조회
   - 포지션 상태 추적
   - 손절가 관리

4. Technical (기술적 분석)
   - EMA(5,20,40) 계산
   - ATR(20) 계산
   - 거래 신호 생성

### 1.2 구현 순서
1. TimeSync
   - 서버 시간 동기화
   - 정확한 업데이트 타이밍

2. DataFeed
   - 완성된 봉 데이터 관리
   - 실시간 업데이트

3. Position
   - MT5 직접 통신
   - 포지션 상태 관리

4. Technical
   - 기술적 지표 계산
   - 거래 신호 생성

### 1.3 테스트 계획
각 모듈별 독립적인 테스트 파일 작성:
- time_sync_test.py
- data_feed_test.py
- position_test.py
- technical_test.py 

### 1.3 백테스팅 전략
1. 백테스팅 프레임워크
   - custom backtrader 사용 (/mt5_backtrader)
   - 실제 거래와 동일한 로직 구현
   - MT5 데이터 직접 사용

2. 백테스팅 요구사항
   - 실제 거래 코드와 최대한 동일한 구조 유지
   - 동일한 클래스와 메서드 사용
   - 실시간/백테스트 모드 전환 가능

3. 구현 고려사항
   - Position 클래스의 공통 인터페이스
   - Technical Analysis 로직 재사용
   - 피라미딩 주문 시뮬레이션
   - 슬리피지 및 수수료 반영

4. 성과 분석
   - 기간별 수익률
   - 최대 낙폭 (MDD)
   - 승률 및 손익비
   - 포지션별 상세 분석

5. 코드 구조   ```
   /mt5_backtrader/
       /core/
           position.py      # Position 클래스 (실거래와 공유)
           technical.py     # Technical Analysis (실거래와 공유)
           backtest.py      # 백테스트 전용 기능
       /data/
           mt5_feed.py      # MT5 데이터 피드
           data_utils.py    # 데이터 처리 유틸리티
       /analysis/
           performance.py   # 성과 분석
           visualization.py # 결과 시각화   ```

6. 실거래 연계
   - 공통 모듈 분리
     * Position 관리
     * Technical Analysis
     * 주문 로직
   
   - 모드 전환 가능한 구조
     * 실시간/백테스트 모드 설정
     * 동일한 메서드 호출
     * 결과 비교 가능

   - 테스트 자동화
     * 신규 기능 백테스트
     * 파라미터 최적화
     * 성능 검증

### 1.4 성과 검증 전략
1. 수익성 지표
   - 절대 수익률
     * 일/주/월/연 수익률
     * 누적 수익 곡선
     * 최대 낙폭 (MDD)
   
   - 상대 수익률
     * 샤프 비율 (Sharpe Ratio)
     * 정보 비율 (Information Ratio)
     * 벤치마크 대비 성과

2. 거래 품질 지표
   - 승률 (Win Rate)
     * 전체 승률
     * 롱/숏 포지션별 승률
     * 심볼별 승률
   
   - 손익비 (Profit Factor)
     * 평균 수익 대 손실 비율
     * 최대 수익/손실 거래
     * 연속 손실 횟수

   - 포지션 분석
     * 평균 보유 기간
     * 피라미딩 성공률
     * 손절 비율

3. 리스크 관리 지표
   - 변동성 분석
     * 일일/주간 변동성
     * 최대 drawdown 기간
     * VaR (Value at Risk)
   
   - 포지션 리스크
     * 심볼별 노출도
     * 최대 포지션 크기
     * 레버리지 수준

4. 실행 품질 지표
   - 주문 실행
     * 슬리피지 분석
     * 체결 지연 시간
     * 주문 실패율
   
   - 시스템 안정성
     * 연결 끊김 빈도
     * 에러 발생률
     * 복구 성공률

5. 검증 방법
   - 실시간 모니터링
     * 실시간 성과 대시보드
     * 주요 지표 알림 설정
     * 위험 한도 모니터링
   
   - 정기 분석
     * 일간 성과 리포트
     * 주간 리스크 분석
     * 월간 전략 검토

6. 개선 프로세스
   - 데이터 수집
     * 모든 거래 기록 저장
     * 시장 상황 기록
     * 에러 로그 분석
   
   - 성과 분석
     * 정량적 지표 분석
     * 패턴/이상 징후 발견
     * 개선점 도출
   
   - 전략 최적화
     * 파라미터 조정
     * 필터 개선
     * 리스크 관리 강화

### 1.5 Trading Edge 전략
1. 기본 개념
   - TE = Win Rate * Average Win - Loss Rate * Average Loss
   - 목표: 일평균 100$ 투자하여 1$ 수익 (TE > 0)

2. 승률 관리
   - 목표 승률: 40% 이상
   - 승률 향상 전략
     * EMA 정/역배열 신뢰도 검증
     * 거래량/변동성 필터 최적화
     * 진입 타이밍 정교화

3. 손익비 관리
   - 목표 손익비: 2.0 이상
   - 손익비 향상 전략
     * ATR 기반 손절폭 최적화
     * 피라미딩을 통한 수익 극대화
     * 적절한 청산 시점 포착

4. 리스크 관리
   - 1회 최대 손실: 계좌의 1%
   - 일일 최대 손실: 계좌의 3%
   - 주간 최대 손실: 계좌의 5%

5. 성과 측정
   - 일간 TE 계산
     * 승률 = 수익 거래 수 / 전체 거래 수
     * 평균 수익 = 총 수익 / 수익 거래 수
     * 평균 손실 = 총 손실 / 손실 거래 수
   
   - 포지션별 분석
     * 롱/숏 포지션 별도 TE 계산
     * 심볼별 TE 계산
     * 시간대별 TE 계산

6. TE 개선 프로세스
   - 데이터 수집
     * 모든 거래의 상세 정보 기록
     * 시장 상황 데이터 수집
     * 실행 품질 데이터 수집
   
   - 분석 및 최적화
     * 승�� 저하 원인 분석
     * 손실 거래 패턴 분석
     * 파라미터 최적화
   
   - 전략 개선
     * 필터 조건 강화/완화
     * 진입/청산 로직 개선
     * 포지션 크기 조정

7. 모니터링 지표
   - 실시간 지표
     * 현재 TE 값
     * 승률 추이
     * 손익비 추이
   
   - 일간 리포트
     * 일간 TE 분석
     * 거래별 상세 분석
     * 개선점 도출
   
   - 주간/월간 리포트
     * 장기 TE 추이
     * 전략 성과 분석
     * 리스크 분석

### 1.6 시스템 구조
1. 폴더 구조   ```
   /241030v1.0/
   ├── core/                     # 핵심 모듈
   │   ├── time_sync.py         # 시간 동기화
   │   ├── data_feed.py         # 데이터 관리
   │   ├── position.py          # 포지션 관리
   │   ├── pyramid.py           # 피라미딩 관리
   │   └── technical.py         # 기술적 분석
   │
   ├── utils/                   # 유틸리티
   │   ├── mt5_wrapper.py       # MT5 API 래퍼
   │   ├── logger.py            # 로깅
   │   └── config.py            # 설정 값
   │
   ├── tests/                   # 테스트
   │   ├── time_sync_test.py    # 시간 동기화 테스트
   │   ├── data_feed_test.py    # 데이터 피드 테스트
   │   ├── position_test.py     # 포지션 관리 테스트
   │   └── technical_test.py    # 기술적 분석 테스트
   │
   ├── analysis/               # 분석 도구
   │   ├── performance.py      # 성과 분석
   │   └── visualization.py    # 시각화
   │
   ├── data/                   # 데이터 저장
   │   ├── trades/            # 거래 기록
   │   ├── logs/              # 로그 파일
   │   └── reports/           # 리포트
   │
   ├── trader.py              # 메인 트레이딩 시스템
   ├── config.yaml            # 설정 파일
   └── design.md              # 설계 문서   ```

2. 주요 파일 설명
   - core/time_sync.py
     * TimeSync 클래스
     * 서버 시간 동기화
     * 정각 대기 기능

   - core/data_feed.py
     * DataFeed 클래스
     * 실시간 데이터 관리
     * 봉 데이터 검증

   - core/position.py
     * Position 클래스
     * PositionManager 클래스
     * 포지션 상태 관리

   - core/pyramid.py
     * PyramidOrder 클래스
     * PyramidManager 클래스
     * 피라미딩 주문 관리

   - core/technical.py
     * TechnicalAnalysis 클래스
     * 지표 계산
     * 신호 생성

   - utils/mt5_wrapper.py
     * MT5 API 래퍼 클래스
     * 에러 처리
     * 재연결 관리

   - utils/logger.py
     * 로깅 설정
     * 에러 로깅
     * 성과 로깅

   - utils/config.py
     * 설정 관리
     * 파라미터 관리
     * 환경 설정

3. 데이터 흐름
   - MT5 서버 → data_feed.py → technical.py → trader.py
   - trader.py → position.py/pyramid.py → MT5 서버
   - 모든 모듈 → logger.py → 로그 파일

4. 설정 관리
   - config.yaml: 전체 설정
   - 환경별 설정 (개발/테스트/운영)
   - 심볼별 설정
   - 전략 파라미터

### 1.7 시스템 흐름도
1. 초기화 흐름   ```
   시작
   ├── MT5 연결
   ├── 설정 파일 로드
   ├── 심볼 목록 확인
   ├── TimeSync 초기화
   ├── DataFeed 초기화
   │   └── 60개 완성된 봉 로드
   ├── PositionManager 초기화
   │   └── 기존 포지션 확인
   └── TechnicalAnalysis 초기화   ```

2. 메인 루프 흐름   ```
   매분 정각(00초)
   ├── 시간 동기화 확인
   ├── MT5 연결 확인
   ├── 데이터 업데이트
   │   ├── 새로운 봉 데이터 요청
   │   ├── 완성된 봉 필터링
   │   └── 데이터 무결성 검증
   │
   ├── 포지션 동기화
   │   ├── MT5 포지션 조회
   │   ├── 자동 청산 감지
   │   └── 포지션 정보 업데이트
   │
   └── 각 심볼별 처리
       ├── 기술적 지표 계산
       │   ├── EMA(5,20,40) 계산
       │   └── ATR(20) 계산
       │
       ├── 포지션 없는 경우
       │   ├── 진입 신호 확인
       │   ├── 거래량/변동성 필터
       │   └── 신규 진입 실행
       │       ├── 포지션 크기 계산
       │       ├── 손절가 설정
       │       └── 피라미딩 주문 설정
       │
       └── 포지션 있는 경우
           ├── 청산 신호 확인
           │   └── 전체 포지션 청산
           │
           ├── 피라미딩 신호 확인
           │   ├── 1/2N 이동 확인
           │   └── 추가 진입 실행
           │
           └── 손절가 관리
               └── 피라미딩시 재조정   ```

3. 데이터 흐름   ```
   MT5 서버
   ├── 시간 데이터  ───→ TimeSync
   ├── 가격 데이터  ───→ DataFeed
   └── 거래 데이터  ───→ PositionManager
                          │
   DataFeed        ────→  │
                          │
   시그널 생성     ←────  │
                          │
   주문 실행       ────→  │
                          ↓
                       MT5 서버   ```

4. 로깅 흐름   ```
   이벤트 발생
   ├── 시스템 로그
   │   ├── 초기화/종료
   │   ├── 에러/경고
   │   └── 연결 상태
   │
   ├── 거래 로그
   │   ├── 진입/청산
   │   ├── 손익 정보
   │   └── 포지션 상태
   │
   └── 성과 로그
       ├── 거래 이력
       ├── 수익률
       └── 리스크 지표   ```

5. 에러 처리 흐름   ```
   에러 발생
   ├── MT5 연결 끊김
   │   ├── 재연결 시도
   │   └── 안전 모드 전환
   │
   ├── 데이터 오류
   │   ├── 데이터 재요청
   │   └── 임시 데이터 사용
   │
   ├── 주문 실패
   │   ├── 원인 분석
   │   └── 재시도 또는 포기
   │
   └── 시스템 오류
       ├── 상태 저장
       ├── 로그 기록
       └── 안전 종료   ```

### 1.8 플랫폼 확장 전략
1. 추상화 계층   ```python
   # 브로커 인터페이스
   class BrokerInterface:
       def initialize(self): pass
       def get_server_time(self): pass
       def get_candles(self, symbol, timeframe, count): pass
       def get_positions(self, symbol): pass
       def place_order(self, order_request): pass
       def modify_order(self, order_request): pass
       def cancel_order(self, order_request): pass
   
   # 표준화된 데이터 구조
   class StandardCandle:
       symbol: str
       timestamp: datetime
       open: float
       high: float
       low: float
       close: float
       volume: float
   
   class StandardPosition:
       ticket: str
       symbol: str
       type: str  # 'BUY' or 'SELL'
       volume: float
       entry_price: float
       sl_price: float   ```

2. 브로커별 구현   ```
   /brokers/
   ├── base/
   │   ├── broker_base.py     # 기본 인터페이스
   │   ├── data_types.py      # 표준 데이터 타입
   │   └── exceptions.py      # 공통 예외 처리
   │
   ├── mt5/
   │   ├── mt5_broker.py      # MT5 구현
   │   ├── mt5_mapper.py      # 데이터 변환
   │   └── mt5_config.py      # 설정
   │
   ├── binance/
   │   ├── binance_broker.py  # 바이낸스 구현
   │   ├── binance_mapper.py  # 데이터 변환
   │   └── binance_config.py  # 설정
   │
   └── upbit/
       ├── upbit_broker.py    # 업비트 구현
       ├── upbit_mapper.py    # 데이터 변환
       └── upbit_config.py    # 설정   ```

3. 데이터 표준화
   - 시간 동기화
     * 모든 시간을 UTC로 통일
     * 브로커별 시간대 처리
     * 타임스탬프 정규화
   
   - 가격 데이터
     * 소수점 자릿수 통일
     * 틱 사이즈 정규화
     * 거래량 단위 변환
   
   - 주문 타입
     * 시장가/지정가 매핑
     * 스탑/리밋 주문 변환
     * 주문 상태 표준화

4. 구현 전략
   - 브로커 추상화
     * 공통 인터페이스 정의
     * 브로커별 구현 분리
     * 의존성 주입 패턴 사용
   
   - 데이터 매핑
     * 브로커별 매퍼 클래스
     * 양방향 데이터 변환
     * 데이터 검증 로직
   
   - 에러 처리
     * 브로커별 에러 매핑
     * 재시도 정책
     * 장애 복구 전략

5. 확장 프로세스
   - 신규 브로커 추가
     * 인터페이스 구현
     * 데이터 매퍼 작성
     * 단위 테스트 작성
   
   - 테스트 절차
     * 연결 테스트
     * 데이터 검증
     * 주문 테스트
     * 통합 테스트

6. 설정 관리
   - 브로커별 설정
     * API 키/시크릿
     * 서버 정보
     * 타임아웃 설정
   
   - 심볼 매핑
     * 심볼 코드 변환
     * 거래단위 변환
     * 수수료 정책

7. 모니터링
   - 연결 상태
     * 브로커별 상태 확인
     * 응답 시간 측정
     * 에러율 모니터링
   
   - 데이터 품질
     * 데이터 지연 확인
     * 가격 이상치 감지
     * 누락 데이터 처리

8. 성능 최적화
   - 연결 관리
     * 커넥션 풀링
     * 웹소켓 활용
     * 배치 처리
   
   - 캐싱 전략
     * 데이터 캐싱
     * 요청 제한 관리
     * 메모리 관리

## 3. 참고 자료
### 3.1 Backtrader 핵심 클래스

1. Strategy 클래스
   - 전략 구현의 기본 클래스
   - 주요 메서드:
     * __init__(): 전략 초기화
     * next(): 매 봉마다 호출
     * notify_order(): 주문 상태 변경시 호출
     * notify_trade(): 거래 상태 변경시 호출
   - 속성:
     * params: 전략 파라미터
     * position: 현재 포지션
     * orders: 주문 목록

2. Order 클래스
   - 주문 상태 관리
   - 주요 상태:
     * Submitted: 주문 제출
     * Accepted: 주문 접수
     * Partial: 부분 체결
     * Completed: 완전 체결
     * Canceled: 주문 취소
     * Expired: 주문 만료
     * Margin: 증거금 부족
     * Rejected: 주문 거부
   - 주문 타입:
     * Market: 시장가
     * Limit: 지정가
     * Stop: 스탑
     * StopLimit: 스탑 리밋

3. Trade 클래스
   - 거래 정보 관리
   - 주요 속성:
     * status: 거래 상태 (Open/Closed)
     * size: 거래 크기
     * price: 진입 가격
     * value: 거래 가치
     * commission: 수수료
     * pnl: 손익
     * pnlcomm: 수수료 포함 손익
     * isclosed: 종료 여부

4. Position 클래스
   - 포지션 상태 관리
   - 주요 속성:
     * size: 포지션 크기
     * price: 평균 진입가
     * adjbase: 조정 기준가
     * closed: 청산된 크기
     * trades: 관련 거래 목록
   - 손익 계산:
     * upopened: 미실현 수량
     * upclosed: 실현 수량
     * pnl: 손익
     * upnl: 미실현 손익

5. Data Feed 클래스
   - 가격 데이터 관리
   - OHLCV 데이터:
     * open: 시가
     * high: 고가
     * low: 저가
     * close: 종가
     * volume: 거래량
     * openinterest: 미결제약정
   - 시간 정보:
     * datetime: 시간
     * date: 날짜
     * time: 시각

6. Broker 클래스
   - 주문 실행 관리
   - 주요 메서드:
     * submit(): 주문 제출
     * buy(): 매수 주문
     * sell(): 매도 주문
     * cancel(): 주문 취소
   - 계좌 정보:
     * cash: 현금
     * value: 자산 가치
     * positions: 포지션 목록

7. Analyzer 클래스
   - 성과 분석
   - 주요 메서드:
     * start(): 분석 시작
     * next(): 매 틱/봉마다 분석
     * stop(): 분석 종료
   - 분석 결과:
     * get_analysis(): 분석 결과 반환

이러한 backtrader의 핵심 클래스들을 참고하여:
1. 실시간 거래와 백테스팅에서 동일하게 사용할 수 있는 인터페이스 설계
2. 주문, 포지션, 거래 관리의 일관성 유지
3. 성과 분석 및 모니터링 기능 구현

### 3.1 TimeSync

[!NOTE] wait_for_next_minute
def wait_for_next_minute(self):
    """다음 분의 정각까지 대기"""
    while True:
        current_time = self.get_server_time()
        seconds = current_time % 60
        if seconds == 0:
            return
        time.sleep(min(1, 60 - seconds))

### 3.2 DataFeed

[!NOTE] update
def update(self):
    """데이터 업데이트"""
    for symbol in self.symbols:
        current_time = self.get_server_time()
        rates = self.get_latest_candles(symbol)
        self.validate_and_store(rates)

### 3.3 Position

[!NOTE] sync_positions
def sync_positions(self):
    """포지션 동기화"""
    mt5_positions = self.get_mt5_positions()
    self.update_positions(mt5_positions)
    self.check_closed_positions()

### 3.4 Pyramid

[!NOTE] place_orders
def place_orders(self, symbol, position):
    """피라미딩 주문 설정"""
    entry_price = position.entry_price
    atr = position.entry_atr
    for i in range(4):
        self.place_pyramid_order(symbol, entry_price, atr, i+1)