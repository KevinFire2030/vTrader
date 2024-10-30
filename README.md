# vTrader

MT5 기반의 자동매매 시스템

## 프로젝트 구조

/vTrader/
├── 241030v1.0/ # 현재 개발 중인 버전
│ ├── core/ # 핵심 모듈
│ │ ├── time_sync.py # 시간 동기화
│ │ ├── data_feed.py # 데이터 관리
│ │ ├── position.py # 포지션 관리
│ │ ├── pyramid.py # 피라미딩 관리
│ │ └── technical.py # 기술적 분석
│ │
│ ├── utils/ # 유틸리티
│ │ ├── mt5_wrapper.py # MT5 API 래퍼
│ │ ├── logger.py # 로깅
│ │ └── config.py # 설정 값
│ │
│ ├── tests/ # 테스트
│ │ ├── time_sync_test.py
│ │ ├── data_feed_test.py
│ │ ├── position_test.py
│ │ └── technical_test.py
│ │
│ ├── trader.py # 메인 트레이딩 시스템
│ ├── config.yaml # 설정 파일
│ ├── design.md # 설계 문서
│ └── implement.md # 구현 계획
│
└── live_trading/ # 이전 버전


## 구현된 기능

### Core Modules
- TimeSync: 서버 시간 동기화 (완료)
  - 서버-로컬 시간 차이 계산
  - 정각(00초) 대기
  - 시간 동기화 상태 모니터링

### 개발 중인 기능
- DataFeed: 실시간 데이터 관리
- Position: 포지션 관리
- Technical: 기술적 분석
- Pyramid: 피라미딩 관리

## 거래 전략

### 진입 전략
- EMA(5,20,40) 정배열/역배열 확인
- 정배열: 롱 포지션 진입
- 역배열: 숏 포지션 진입
- 추가 필터: 거래량, 변동성 확인

### 피라미딩 전략
- 신규 진입 후 자동 피라미딩 주문 설정
- 4개의 피라미딩 주문 동시 설정
- 각 주문의 간격: 1/2N (ATR 기반)
- 심볼당 최대 4유닛 제한

### 리스크 관리
- 1유닛 = 계좌의 1% 리스크
- 최대 리스크 = 계좌의 30% (15유닛)
- 심볼당 최대 리스크 = 계좌의 8% (4유닛)

## 설치 및 실행

### 요구사항
- Python 3.8 이상
- MetaTrader5
- pandas
- pandas_ta
- numpy

### 설치

bash
git clone https://github.com/your-username/vTrader.git
cd vTrader
pip install -r requirements.txt


### 실행

bash
cd 241030v1.0/tests
python -m pytest

## 문서
- [설계 문서](241030v1.0/design.md)
- [구현 계획](241030v1.0/implement.md)

## 라이선스
MIT License