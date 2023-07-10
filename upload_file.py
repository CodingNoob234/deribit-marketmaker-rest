#!/usr/bin/python3
from pyicloud import PyiCloudService
import pandas as pd
# api = PyiCloudService('joeybesseling@icloud.com')

def UploadFile(df, instrument):

    # existing_files = api.drive["Documents"]["Programmeren"]["Projects"]["Data"][instrument].dir()
    
    # # determine first non-existing file
    # i = 1
    # av = False
    # while not av:
    #     if instrument.upper() + f"_1_20({i}).parquet" in existing_files:
    #         i += 1
    #     else: av = True
    
    # # store
    # df.to_parquet(f"/Users/")
    # df.to_parquet(f'~/Data/{instrument.upper()}_1_20({i}).parquet')
    # with open(f'~/Data/{instrument.upper()}_1_20({i}).parquet', 'rb') as file:
    #     api.drive["Documents"]["Programmeren"]["Projects"]["Data"][instrument].upload(file)

    path = f"/Users/joeybesseling/Documents/Programmeren/Projects/Data/{instrument.upper()}/"
    av = False
    i = 0
    while not av:
        try: 
            pd.read_parquet(path + instrument.upper() + f"_1_20({i}).parquet")
            i += 1
        except:
            df['timestamp'] =df['timestamp'].astype('datetime64[s]')
            df.to_parquet(path + instrument.upper() + f"_1_20({i}).parquet") 
            av = True