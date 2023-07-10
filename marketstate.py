import pandas as pd

class MarketState():
    def __init__(self,):
        # create empty dataframe
        data = {"timestamp": []}
        for i in range(1,20+1):
            data[f"bid{i}_price"] = []
            data[f"bid{i}_size"] = []
            data[f"ask{i}_price"] = []
            data[f"ask{i}_size"] = []
        data["trade_num"] = []
        data["trade_vol"] = []
        data["trade_num_buy"] = []
        data["trade_vol_buy"] = []
        data["trade_num_sell"] = []
        data["trade_vol_sell"] = []
        self.df = pd.DataFrame(data)
        self.i = 0
        
    def __call__(self,):
        return self.df
    
    def add_line(self,line):
        self.df.loc[self.i] = line
        self.i += 1