import numpy as np
import pandas as pd
from threading import Thread
import time
from deribitv2 import DeriBit
from upload_file import UploadFile

instrument = "ETH-PERPETUAL"
interval = 1
depth = 20
save_location = "data_connected/"

def fetch_data(instrument, interval, depth):
    try:
        # connect with api
        d = DeriBit()
        d.getauth()

        # create empty dataframe
        data = {"timestamp": []}
        for i in range(1,depth+1):
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
        df = pd.DataFrame(data)

        i = 0
        ended_at = time.time()
        started_at_previous = time.time()
        while df.shape[0] < 250000: # 250000
            started_at = time.time()

            # request book
            book = d.getorderbook(instrument)
            bids_asks = [[book["bids"][i][0], book["bids"][i][1], book["asks"][i][0], book["asks"][i][1]] for i in range(depth)]
            book_data = []
            for bid_ask in bids_asks:
                book_data += bid_ask

            # request recent trades
            trades = d.getlasttrades_bytime(instrument, start_timestamp=int(started_at_previous*1000), end_timestamp=int(started_at*1000))['trades']
            trade_data = []
            trade_data += [len(trades), sum([t["amount"] for t in trades])]

            # seperate for buy and sell
            trades_buy = [t for t in trades if t["direction"] == "buy"]
            trades_sell = [t for t in trades if t["direction"] == "sell"]
            trade_data += [len(trades_buy), sum([t["amount"] for t in trades_buy])]
            trade_data += [len(trades_sell), sum([t["amount"] for t in trades_sell])]

            # add to df
            df.loc[i] = [pd.to_datetime(started_at, unit = 's')] + book_data + trade_data
            i += 1

            update_command(i, 250000)

            ended_at = time.time()
            if ended_at - d.last_refresh > 850:
                d.getauth()
            if interval - (ended_at - started_at) > 0:
                time.sleep(interval - (ended_at - started_at))
            else:
                print(f"Warning: Interval might be too short as request takes longer ({round(ended_at - started_at,3)}) than interval at {pd.to_datetime(time.time(), unit='s')}.")
            started_at_previous = started_at
        if df.shape[0] > 3600: # 3600
            available = False
            UploadFile(df, instrument)
    except Exception as e:
        print(e)
        if df.shape[0] > 3600:
            available = False
            UploadFile(df, instrument)

def fetch_data_loop(instrument):
    interval = 1
    depth = 20
    while True:
        try:
            fetch_data(instrument, interval, depth)
        except Exception as e:
            time.sleep(60)

def update_command(progress, total):    
    print(f"\r {progress}/{total}", end="\r")

if __name__ == "__main__":
    instruments = ("ETH-PERPETUAL", "ETH_USDC-PERPETUAL","BTC-PERPETUAL", "BTC_USDC-PERPETUAL")
    valid = False
    while not valid:
        instrument = input("Instrument: ")
        if instrument in instruments:
            valid = True
    fetch_data_loop(instrument)