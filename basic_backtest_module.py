import sys, pathlib, os, logging
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
sys.path.append(f"{str(working_dir)}/config")
from google.cloud import storage
from config import pw
import pandas as pd
from binance.client import Client
from binance import Client
from binance.enums import *
from tools import discorder, vm
import pandas as pd
import numpy as np
from operator import sub
from datetime import datetime

logging.basicConfig(level=logging.INFO,format="%(asctime)s : %(message)s")
#_______________________________________________________________________________

def create_df_kline(symbol, timeFrame, days):
    binance_client = Client(pw.binance_api_key, pw.binance_api_secret)

    logging.info(f"Fetching data for __{symbol}__ for {days} days from Binance.")

    if timeFrame == 1:
        kline_timeFrame = Client.KLINE_INTERVAL_1MINUTE
    if timeFrame == 5:
        kline_timeFrame = Client.KLINE_INTERVAL_5MINUTE
    if timeFrame == 15:
        kline_timeFrame = Client.KLINE_INTERVAL_15MINUTE
    if timeFrame == 30:
        kline_timeFrame = Client.KLINE_INTERVAL_30MINUTE
    if timeFrame == 60:
        kline_timeFrame = Client.KLINE_INTERVAL_1HOUR
    if timeFrame == 120:
        kline_timeFrame = Client.KLINE_INTERVAL_2HOUR
    if timeFrame == 240:
        kline_timeFrame = Client.KLINE_INTERVAL_4HOUR
    if timeFrame == 360:
        kline_timeFrame = Client.KLINE_INTERVAL_6HOUR
    if timeFrame == 720:
        kline_timeFrame = Client.KLINE_INTERVAL_12HOUR
    if timeFrame == 1440:
        kline_timeFrame = Client.KLINE_INTERVAL_1DAY

    data = binance_client.futures_historical_klines(symbol, kline_timeFrame, f"{days} day ago UTC")

    df_kline = pd.DataFrame(data, columns = ['openTime','open','high','low','close','volume','closeTime',\
        'quoteAssetVolume','trades','takerBuyBaseAssetVolume','takerBuyQuoteAssetVolume','Ignore'])

    # df_kline['openTime'] = pd.to_datetime((df_kline['openTime']/1000).astype(int), unit='s')
    df_kline['openTime'] = df_kline['openTime']/1000

    df_kline = df_kline.tail(1440*days)

    del df_kline["open"], df_kline['closeTime'], df_kline["quoteAssetVolume"], df_kline["trades"],\
        df_kline["takerBuyBaseAssetVolume"], df_kline["takerBuyQuoteAssetVolume"], df_kline['Ignore']
    
    df_kline = df_kline.reset_index(drop=True)
    
    # start = df_kline.iloc[0,0]
    # end   = df_kline.iloc[-1,0]

    return df_kline
#_______________________________________________________________________________
def create_df_backtest(backtest_result):

    result_0 = [item[0] for item in backtest_result]
    result_1 = [item[1] for item in backtest_result]
    result_2 = [item[2] for item in backtest_result]
    result_3 = [item[3] for item in backtest_result]
    result_4 = [item[4] for item in backtest_result]
    result_5 = [item[5] for item in backtest_result]
    result_6 = [item[6] for item in backtest_result]

    result_columns = {'PARAMS_SERIES':[],'UNFINISHED_profit':[],'NET_profit_SERIES':[],'PAPER_LOSS_SERIES':[],'PAPER_profit_SERIES':[],'ENTRY_TIME_SERIES':[],'EXIT_TIME_SERIES':[]}

    df_bt_result = pd.DataFrame(list(zip(result_0, result_1,result_2,result_3,result_4,result_5, result_6)),columns = result_columns)

    return df_bt_result

#________________________________________________________________________________

def upload_googleCloudStorage(df_bt_result,stage,strategy,activationTime,symbol):

    os.makedirs(f"{working_dir}/static/{stage}/{strategy}/{activationTime}", exist_ok=True)

    client_storage = storage.Client()
    bucket_name    = "project_bucket"
    bucket         = client_storage.get_bucket(bucket_name)

    googleCloudStorage_path = f'{stage}/{strategy}/{activationTime}/{symbol}.csv'
    local_path = f'{working_dir}/static/{googleCloudStorage_path}'

    df_bt_result.to_csv(local_path, index=False)

    blob_data = bucket.blob(googleCloudStorage_path)
    blob_data.upload_from_filename(local_path)  
#____________________________________________________________

def func_backtest_entry(index,close,backtestPyramiding,entryTimes,time_data):

    indexEntry = index
    entryPrice = close
    backtestPyramiding = 1
    entryTimes.append(time_data) 

    return indexEntry, entryPrice, backtestPyramiding,entryTimes,time_data
#____________________________________________________________

def func_backtest_exit( side,
                        index,
                        close,
                        backtestPyramiding,
                        list_netp,
                        exitTimes,
                        list_paperLoss,
                        time_data,
                        entryPrice,
                        indexEntry,
                        indexExit,
                        dataHigh,
                        dataLow):

    indexExit = index
    exitPrice = close
    backtestPyramiding = 0

    exitTimes.append(time_data)

    worstPrice = entryPrice

    for x in range(indexEntry, indexExit):

        # temp_Best = dataHigh[x] if side == "L" else dataLow[x]
        if side == "L":
            # print("side is L")
            temp_Worst = dataLow[x]  
            # print(f"temp_Worst is {temp_Worst}")

            # FIXME: THis is not working. maybe, index is fucked up. I dont know what to do...
            if temp_Worst < worstPrice:
                worstPrice = temp_Worst 
                print(f"worstPrice is {worstPrice}")
        else:
            temp_Worst = dataHigh[x]
            if temp_Worst > worstPrice:
                worstPrice = temp_Worst 

    #     # # if temp_Best < BestPrice:
    #     # #     BestPrice = temp_Best 

    if side == "L":

        profit = (1-(entryPrice/exitPrice))*100 

        worstPrice = 1

        paperLoss = (1-(entryPrice/worstPrice))*100

        paperLoss = 999
        
        list_netp.append(round(profit,2))
        list_paperLoss.append(round(paperLoss,2))

    # elif side == "S":

    #     list_netp.append(round((entryPrice/exitPrice)-1)*100,2) 

    

    return indexExit,exitPrice,backtestPyramiding,list_netp,exitTimes,list_paperLoss

#__________________________________________________________________

def param1Range(param1_min, param1_max, param1_cut):
    param1_step  = int((param1_max - param1_min) /param1_cut)
    range_param1 = np.arange(param1_min, param1_max+1, param1_step)
    return range_param1

def param2Range(param2_min, param2_max, param2_cut):
    param2_step  = int((param2_max - param2_min) /param2_cut)
    range_param2 = np.arange(param2_min, param2_max+1, param2_step)
    return range_param2

def param3Range(param3_min, param3_max, param3_cut):
    param3_step  = int((param3_max - param3_min) /param3_cut)
    range_param3 = np.arange(param3_min, param3_max+1, param3_step)
    return range_param3

def param4Range(param4_min, param4_max, param4_cut):
    param4_step = int((param4_max - param4_min) / param4_cut)
    range_param4 = np.arange(param4_min, param4_max+1, param4_step)
    return range_param4