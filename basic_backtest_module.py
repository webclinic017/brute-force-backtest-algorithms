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

def create_df_kline(Symbol, TimeFrame, days):
    binance_client = Client(pw.binance_api_key, pw.binance_api_secret)

    logging.info(f"Fetching data for __{Symbol}__ for {days} days from Binance.")

    if TimeFrame == 1:
        kline_TimeFrame = Client.KLINE_INTERVAL_1MINUTE
    if TimeFrame == 5:
        kline_TimeFrame = Client.KLINE_INTERVAL_5MINUTE
    if TimeFrame == 15:
        kline_TimeFrame = Client.KLINE_INTERVAL_15MINUTE
    if TimeFrame == 30:
        kline_TimeFrame = Client.KLINE_INTERVAL_30MINUTE
    if TimeFrame == 60:
        kline_TimeFrame = Client.KLINE_INTERVAL_1HOUR
    if TimeFrame == 120:
        kline_TimeFrame = Client.KLINE_INTERVAL_2HOUR
    if TimeFrame == 240:
        kline_TimeFrame = Client.KLINE_INTERVAL_4HOUR
    if TimeFrame == 360:
        kline_TimeFrame = Client.KLINE_INTERVAL_6HOUR
    if TimeFrame == 720:
        kline_TimeFrame = Client.KLINE_INTERVAL_12HOUR
    if TimeFrame == 1440:
        kline_TimeFrame = Client.KLINE_INTERVAL_1DAY

    Data = binance_client.futures_historical_klines(Symbol, kline_TimeFrame, f"{days} day ago UTC")

    df_kline = pd.DataFrame(Data, columns = ['OpenTime','Open','High','Low','Close','Volume','CloseTime',\
        'QuoteAssetVolume','Trades','TakerBuyBaseAssetVolume','TakerBuyQuoteAssetVolume','Ignore'])

    # df_kline['OpenTime'] = pd.to_datetime((df_kline['OpenTime']/1000).astype(int), unit='s')
    df_kline['OpenTime'] = df_kline['OpenTime']/1000

    df_kline = df_kline.tail(1440*days)

    del df_kline["Open"], df_kline['CloseTime'], df_kline["QuoteAssetVolume"], df_kline["Trades"],\
        df_kline["TakerBuyBaseAssetVolume"], df_kline["TakerBuyQuoteAssetVolume"], df_kline['Ignore']
    
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

    result_columns = {'PARAMS_SERIES':[],'UNFINISHED_PROFIT':[],'NET_PROFIT_SERIES':[],'PAPER_LOSS_SERIES':[],'PAPER_PROFIT_SERIES':[],'ENTRY_TIME_SERIES':[],'EXIT_TIME_SERIES':[]}

    df_bt_result = pd.DataFrame(list(zip(result_0, result_1,result_2,result_3,result_4,result_5, result_6)),columns = result_columns)

    return df_bt_result

#________________________________________________________________________________

def upload_gcs(df_bt_result,stage,Strategy,ActivationTime,Symbol):

    os.makedirs(f"{working_dir}/static/{stage}/{Strategy}/{ActivationTime}", exist_ok=True)

    client_storage = storage.Client()
    bucket_name    = "bankof3v_bucket"
    bucket         = client_storage.get_bucket(bucket_name)

    GCS_path = f'{stage}/{Strategy}/{ActivationTime}/{Symbol}.csv'
    LOCAL_path = f'{working_dir}/static/{GCS_path}'

    df_bt_result.to_csv(LOCAL_path, index=False)

    blob_data = bucket.blob(GCS_path)
    blob_data.upload_from_filename(LOCAL_path)  
#____________________________________________________________

def func_backtest_entry(index,Close,backtest_pyramiding,EntryTimes,Time):

    index_Entry = index
    Entry_Price = Close
    backtest_pyramiding = 1
    EntryTimes.append(Time) 

    return index_Entry, Entry_Price, backtest_pyramiding,EntryTimes,Time
#____________________________________________________________

def func_backtest_exit( side,
                        index,
                        Close,
                        backtest_pyramiding,
                        list_NetP,
                        ExitTimes,
                        list_paperLoss,
                        Time,
                        Entry_Price,
                        index_Entry,
                        index_Exit,
                        data_High,
                        data_Low):

    index_Exit = index
    Exit_Price = Close
    backtest_pyramiding = 0

    ExitTimes.append(Time)

    WorstPrice = Entry_Price

    for x in range(index_Entry, index_Exit):

        # temp_Best = data_High[x] if side == "L" else data_Low[x]
        if side == "L":
            # print("side is L")
            temp_Worst = data_Low[x]  
            # print(f"temp_Worst is {temp_Worst}")

            # FIXME: THis is not working. maybe, index is fucked up. I dont know what to do...
            if temp_Worst < WorstPrice:
                WorstPrice = temp_Worst 
                print(f"WorstPrice is {WorstPrice}")
        else:
            temp_Worst = data_High[x]
            if temp_Worst > WorstPrice:
                WorstPrice = temp_Worst 

    #     # # if temp_Best < BestPrice:
    #     # #     BestPrice = temp_Best 

    if side == "L":

        Profit = (1-(Entry_Price/Exit_Price))*100 

        WorstPrice = 1

        paperLoss = (1-(Entry_Price/WorstPrice))*100

        paperLoss = 999
        
        list_NetP.append(round(Profit,2))
        list_paperLoss.append(round(paperLoss,2))

    # elif side == "S":

    #     list_NetP.append(round((Entry_Price/Exit_Price)-1)*100,2) 

    

    return index_Exit,Exit_Price,backtest_pyramiding,list_NetP,ExitTimes,list_paperLoss

#__________________________________________________________________

def P1_Range(P1_min, P1_max, P1_cut):
    P1_step  = int((P1_max - P1_min) /P1_cut)
    range_P1 = np.arange(P1_min, P1_max+1, P1_step)
    return range_P1

def P2_Range(P2_min, P2_max, P2_cut):
    P2_step  = int((P2_max - P2_min) /P2_cut)
    range_P2 = np.arange(P2_min, P2_max+1, P2_step)
    return range_P2

def P3_Range(P3_min, P3_max, P3_cut):
    P3_step  = int((P3_max - P3_min) /P3_cut)
    range_P3 = np.arange(P3_min, P3_max+1, P3_step)
    return range_P3

def P4_Range(P4_min, P4_max, P4_cut):
    P4_step = int((P4_max - P4_min) / P4_cut)
    range_P4 = np.arange(P4_min, P4_max+1, P4_step)
    return range_P4