import numpy as np
import pandas as pd
from project.scripts.feature_engineering import feature_functions
from time import time
from numba import jit

feature_func = feature_functions["15_dir"]
def feature_engineer(df):
    features = feature_func(df)
    mid = (df["bid1_price"] + df["ask1_price"])/2
    targets_dir = pd.DataFrame({"targets": (mid.apply(np.log).diff()).shift(-1)})
    targets = pd.DataFrame({"targets": (mid.apply(np.log).diff()**2).shift(-1)})
    # features = features[targets != 0]
    # targets = targets[targets!=0]
    # targets = np.log(targets)
    return features, targets, targets_dir

found = True

feature_frames = []
target_frames = []
target_dir_frames = []

instrument = "ETH-PERPETUAL"
path = f"/Users/joeybesseling/Documents/Programmeren/Projects/Data/{instrument}/"
instrument = f"{instrument}"
interval = 1
depth = 20

s = time()
for i in range(55, 83):
    try:
        df = pd.read_parquet(path + f"{instrument}_1_{depth}({i}).parquet")
        df["timestamp"] = pd.to_datetime(df.timestamp)
        df = df.set_index("timestamp", drop = True)
        try: df = df.drop("Unnamed: 0", axis = 1)
        except: pass
        if interval > 1:
            for column in df.columns:
                if "trade" in column:
                    df[column] = df[column].rolling(interval).sum()
        df = df.resample(f"{interval}s").last()
        features, targets, targets_dir = feature_engineer(df)
        features = features[targets["targets"].notna()]
        targets_dir = targets_dir[targets["targets"].notna()]
        targets = targets[targets["targets"].notna()]
        feature_frames.append(features.copy())
        target_frames.append(targets.copy())
        target_dir_frames.append(targets_dir.copy())
    except Exception as e: print(e)
    print(i)
features = pd.concat(feature_frames)
targets = pd.concat(target_frames)
targets_dir = pd.concat(target_dir_frames)

print(time() - s)

path = f"/Users/joeybesseling/Documents/Programmeren/Projects/Data/PROCESSED_{instrument}/"
features.to_parquet(path + f"processed_features_{instrument}_{interval}s.parquet")
targets.to_parquet(path + f"processed_targets_{instrument}_{interval}s.parquet")
targets_dir.to_parquet(path + f"processed_targets_dir_{instrument}_{interval}s.parquet")