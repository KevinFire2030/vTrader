class DataFeed:
    def __init__(self, symbols):
        print("DataFeed 초기화")
        self.symbols = symbols
        self.data_dict = {}
        self._initialize_data()
        
    def _initialize_data(self):
        print("_initialize_data: 초기 60개 봉 로드")
        pass
        
    def update(self):
        print("update: 새로운 봉 데이터 업데이트")
        pass
        
    def get_data(self, symbol):
        print(f"get_data: {symbol} 데이터 조회")
        return None 