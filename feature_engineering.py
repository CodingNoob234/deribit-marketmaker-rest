import numpy as np
import pandas as pd

def rat(df, n):
    return (sum_up(df, "bid", n) - sum_up(df, "ask", n)) / (sum_up(df, "bid", n) + sum_up(df, "ask", n))

def rat_weighted(df, n):
    return (sum_up_weighted(df, "bid", n) + sum_up_weighted(df, "ask", n)) / (sum_up_weighted(df, "bid", n) - sum_up_weighted(df, "ask", n))

def sum_up(df, side, n):
    tot = df[f"{side}1_size"].copy()
    for i in range(2, n + 1):
        tot += df[f"{side}{i}_size"].copy()
    return tot

# @jit(nopython=True)
def sum_up_weighted(df, side, n):
    tot = np.log(df[f'{side}1_size'].copy()) * 1/(mid - df[f"{side}1_price"])
    for i in range(2, n + 1):
        tot += np.log(df[f'{side}{i}_size'].copy()) * 1/(mid - df[f"{side}1_price"])
    return tot

# refresh: 5s | forecast: 5s
def feature_engineer_15_dir(df):
    columns = ["bid1_price", "bid1_size", "ask1_price", "ask1_size", "bid2_price", "bid2_size", "ask2_price", "ask2_size", "trade_vol", "trade_num", "trade_num_buy", "trade_vol_buy", "trade_num_sell", "trade_vol_sell"]
    keys = []

    mid = (df["bid1_price"] + df["ask1_price"])/2

    for column in df.columns:
        if "trade" in column:
            df[column] = df[column].fillna(0)
    
    # # cumulative depths
    df["bid5cum_size"] = np.log(sum_up(df, "bid", 5))
    df["ask5cum_size"] = np.log(sum_up(df, "ask", 5))
    df["bid10cum_size"] = np.log(sum_up(df, "bid", 10))
    df["ask10cum_size"] = np.log(sum_up(df, "ask", 10))
    df["bid20cum_size"] = np.log(sum_up(df, "bid", 20))
    df["ask20cum_size"] = np.log(sum_up(df, "ask", 20))
    keys += ["bid5cum_size", "ask5cum_size","bid10cum_size", "ask10cum_size","bid20cum_size", "ask20cum_size"]

    # # rolling average cumulative depths
    df["bid20cum_size_ma60"] = df["bid20cum_size"].rolling(60).apply(np.mean)
    df["ask20cum_size_ma60"] = df["ask20cum_size"].rolling(60).apply(np.mean)
    keys += ["bid20cum_size_ma60", "ask20cum_size_ma60"]
    
    # # bid/ask ratios
    df["rat1"] = rat(df.copy(), 1)
    df["rat3"] = rat(df.copy(), 3)
    df["rat10"] = rat(df.copy(), 10)
    keys += ["rat1", "rat3", "rat10"]

    # # rat moving average
    df["rat1_ma5"] = df["rat1"].rolling(5).apply(np.mean)
    df["rat3_ma5"] = df["rat3"].rolling(5).apply(np.mean)
    df["rat3_ma5_std"] = df["rat3"].rolling(5).apply(np.std)
    keys += ["rat1_ma5", "rat3_ma5", "rat3_ma5_std"]

    # # ratio of volume versus orderbook liquidity
    df["trade_book_ratio"] = df["trade_vol"] / (df["bid20cum_size"] + df["ask20cum_size"])
    df["trade_book_buy_ratio"] = df["trade_vol_buy"] / df["ask20cum_size"]
    df["trade_book_sell_ratio"] = df["trade_vol_sell"] / df["bid20cum_size"]
    keys += ["trade_book_ratio", "trade_book_buy_ratio", "trade_book_sell_ratio"]
    df["trade_book_ratio_ma15"] = df["trade_book_ratio"].rolling(15).apply(np.mean)
    df["trade_book_buy_ratio_ma15"] = df["trade_book_buy_ratio"].rolling(15).apply(np.mean)
    df["trade_book_sell_ratio_ma15"] = df["trade_book_sell_ratio"].rolling(15).apply(np.mean)
    keys += ["trade_book_ratio_ma15", "trade_book_buy_ratio_ma15", "trade_book_sell_ratio_ma15"] 

    # # volume moving average
    df["trade_vol_5"] = df["trade_vol"].rolling(5).sum()
    df["trade_vol_15"] = df["trade_vol"].rolling(15).sum()
    df["trade_vol_60"] = df["trade_vol"].rolling(60).sum()
    keys += ["trade_vol_5", "trade_vol_15", "trade_vol_60"]

    # # VWAP difference from current mid
    df["MA3_diff"] = mid - mid.rolling(3).apply(np.mean)
    df["MA30_diff"] = mid - mid.rolling(30).apply(np.mean)
    df["MA30_diff_std"] = df["MA30_diff"].rolling(30).apply(np.std)
    keys += ["MA3_diff", "MA30_diff", "MA30_diff_std"]

    # # buy VWAP vs sell VWAP
    VWAP_buy_10 = (df["trade_vol_buy"] * df["ask1_price"]).rolling(10).sum() / df["trade_vol_buy"].rolling(10).sum()
    VWAP_sell_10 = (df["trade_vol_sell"] * df["bid1_price"]).rolling(10).sum() / df["trade_vol_sell"].rolling(10).sum()
    df["VWAP_buy_sell_diff"] = VWAP_buy_10 - VWAP_sell_10
    keys += ["VWAP_buy_sell_diff"]

    # volatility
    mid1 = mid.apply(np.log).diff()
    vol = mid1
    df["d_0"] = vol
    df["d_1"] = vol.shift(1)
    df["d_2"] = vol.shift(2)
    df["d_3"] = vol.shift(3)
    df["d_4"] = vol.shift(4)
    df["d_5"] = vol.shift(5)
    df["d_6"] = vol.shift(6)
    df["d_7"] = vol.shift(7)
    df["d_8"] = vol.shift(8)
    df["d_9"] = vol.shift(9)
    df["d_10"] = vol.shift(10)
    df["d_11"] = vol.shift(11)
    keys += ["d_0", "d_1", "d_2", "d_3", "d_4", "d_5", "d_6", "d_7", "d_8", "d_9", "d_10", "d_11"]
    vol = mid1**2
    df["vol_0"] = vol
    df["vol_1"] = vol.shift(1)
    df["vol_2"] = vol.shift(2)
    df["vol_3"] = vol.shift(3)
    df["vol_4"] = vol.shift(4)
    df["vol_5"] = vol.shift(5)
    df["vol_6"] = vol.shift(6)
    df["vol_7"] = vol.shift(7)
    df["vol_8"] = vol.shift(8)
    df["vol_9"] = vol.shift(9)
    df["vol_10"] = vol.shift(10)
    df["vol_11"] = vol.shift(11)
    keys += ["vol_0", "vol_1", "vol_2", "vol_3", "vol_4", "vol_5", "vol_6", "vol_7", "vol_8", "vol_9", "vol_10", "vol_11"]

    # wigs
    wig_per = 5
    df["wig_up_5"] = (mid.rolling(wig_per).max() - np.maximum(mid, mid.shift(wig_per)))/np.maximum(mid, mid.shift(wig_per))
    df["wig_down_5"] = (mid.rolling(wig_per).min() - np.minimum(mid, mid.shift(wig_per)))/np.minimum(mid, mid.shift(wig_per))
    wig_per = 15
    df["wig_up_15"] = (mid.rolling(wig_per).max() - np.maximum(mid, mid.shift(wig_per)))/np.maximum(mid, mid.shift(wig_per))
    df["wig_down_15"] = (mid.rolling(wig_per).min() - np.minimum(mid, mid.shift(wig_per)))/np.minimum(mid, mid.shift(wig_per))
    wig_per = 60
    df["wig_up_60"] = mid.rolling(wig_per).max() - np.maximum(mid, mid.shift(wig_per))
    df["wig_down_60"] = mid.rolling(wig_per).min() - np.minimum(mid, mid.shift(wig_per))
    keys += ["wig_up_5", "wig_down_5", "wig_up_15", "wig_down_15", "wig_up_60", "wig_down_60"]

    # compute features and targets
    features = df[columns + keys]
    return features

def feature_engineer_15_vol(df):
    columns = ["bid1_price", "bid1_size", "ask1_price", "ask1_size", "bid2_price", "bid2_size", "ask2_price", "ask2_size", "trade_vol", "trade_num", "trade_num_buy", "trade_vol_buy", "trade_num_sell", "trade_vol_sell"]
    keys = []

    def rat(df, n):
        return (sum_up(df, "bid", n) - sum_up(df, "ask", n)) / (sum_up(df, "bid", n) + sum_up(df, "ask", n))

    def sum_up(df, side, n):
        tot = df[f'{side}1_size'].copy()
        for i in range(2, n + 1):
            tot += df[f'{side}{i}_size'].copy()
        return tot

    for column in df.columns:
        if "trade" in column:
            df[column] = df[column].fillna(0)

    # bid/ask ratios
    df["rat1"] = rat(df.copy(), 1)
    df["rat3"] = rat(df.copy(),3)
    df["rat5"] = rat(df.copy(), 5)
    df["rat10"] = rat(df.copy(), 10)
    df["rat20"] = rat(df.copy(), 20)
    keys += ["rat1", "rat3", "rat10", "rat20"]

    # rat moving average
    df["rat1_ma5"] = df["rat1"].rolling(5).apply(np.mean)
    df["rat3_ma5"] = df["rat3"].rolling(5).apply(np.mean)
    df["rat3_ma5_std"] = df["rat3"].rolling(5).apply(np.std)
    keys += ["rat1_ma5", "rat3_ma5", "rat3_ma5_std"]

    # VWAP difference from current mid
    mid = (df["bid1_price"] + df["ask1_price"])/2
    df["MA9_diff"] = mid - mid.rolling(9).apply(np.mean)
    df["MA3_diff"] = mid - mid.rolling(3).apply(np.mean)
    df["MA30_diff"] = mid - mid.rolling(30).apply(np.mean)
    keys += ["MA9_diff", "MA3_diff", "MA30_diff"]

    # # volatility
    mid1 = mid.apply(np.log).diff()
    vol = mid1**2
    df["vol_0"] = vol
    df["vol_1"] = vol.shift(1)
    df["vol_2"] = vol.shift(2)
    df["vol_3"] = vol.shift(3)
    df["vol_4"] = vol.shift(4)
    df["vol_5"] = vol.shift(5)
    df["vol_6"] = vol.shift(6)
    df["vol_7"] = vol.shift(7)
    df["vol_8"] = vol.shift(8)
    df["vol_9"] = vol.shift(9)
    df["vol_10"] = vol.shift(10)
    df["vol_11"] = vol.shift(11)
    keys += ["vol_0", "vol_1", "vol_2", "vol_3", "vol_4", "vol_5", "vol_6", "vol_7", "vol_8", "vol_9", "vol_10", "vol_11"]

    # compute features and targets
    features = df[columns + keys]
    return features


feature_functions = {
    "15_dir": feature_engineer_15_dir,
    "15_vol": feature_engineer_15_dir, 
}
