import sys, pathlib
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
sys.path.append(f"{str(working_dir)}/config")
sys.path.append(f"{str(working_dir)}/strategy")
sys.path.append(f"{str(working_dir)}/views")
from config import pw
from binance import Client

import pandas as pd
import pandas_ta as ta
import numpy as np

import datetime, os, logging, sys
from google.cloud import storage
from config import binance_data
from tools import discorder, vm
logging.basicConfig(level=logging.INFO,format="%(asctime)s : %(message)s")

def create_df(df):

    hours = 60    # don't change value
    days  = 1440  # don't change value

    input_TR_length  = int( 12*hours /60)
    input_ATR_length = int( 14*days  /60)
    input_Vol_Rapid  = int( 12*hours /60)
    input_Vol_Slow   = int( 14*days  /60)
    input_VolumeUSD  = int( 30*days  /60)
    
    df["HighestRange"] = df["High"].rolling(input_TR_length).max()
    df["LowestRange"]  = df["Low"].rolling(input_TR_length).min()
    df["NATR"]         = ta.natr(df[f"HighestRange"], df[f"LowestRange"], df["Close"].shift(1), length=input_ATR_length)
    df["Rapid_Vol"]    = ta.sma(df["VolumeUSD"], length = input_Vol_Rapid)
    df["Slow_Vol"]     = ta.sma(df["VolumeUSD"], length = input_Vol_Slow)
    df["VolRatio"]     = ((df["Rapid_Vol"]/df["Slow_Vol"])*100)-100
    df["VolUSD_SMA"]    = ta.sma(df["VolumeUSD"], length = input_VolumeUSD)

    return df

#--------------------------------------------------------------------------------

def run(debug, ActivationTime, discord_server):

    if debug == True:
        list_Symbol = ["BTCUSDT", "ETHUSDT"]
        df_screened = pd.DataFrame({'Ticker':list_Symbol, 'NATR':[0,0], 'VolRatio':[0,0], 'VolUSD_SMA':[0,0]})

    else:
        os.makedirs(f"{working_dir}/static/SCREEN/{ActivationTime}", exist_ok=True)

        list_Symbol = binance_data.fetch_all_symbols()

        list_NATR       = []
        list_VolRatio   = []
        list_VolUSD_SMA = []

        for Ticker in list_Symbol:
            try:
                df = kline(Ticker, 33, Client.KLINE_INTERVAL_1HOUR)

                df = create_df(df)

                df.drop(columns=['HighestRange','LowestRange','Rapid_Vol','Slow_Vol'], inplace=True)
                df.drop(columns=['CloseTime','Ignore'], inplace=True)
                df.dropna(inplace=True)

                value_NATR     = round(df.iloc[-1]["NATR"],2)
                value_VolRatio = round(df.iloc[-1]["VolRatio"],2)
                value_VolUSD_SMA = round(df.iloc[-1]["VolUSD_SMA"],2)

                list_NATR.append(value_NATR)
                list_VolRatio.append(value_VolRatio)
                list_VolUSD_SMA.append(value_VolUSD_SMA)

            except:
                list_NATR.append("NaN")
                list_VolRatio.append("NaN")
                list_VolUSD_SMA.append("NaN")
                continue

        df_screened = pd.DataFrame({'Ticker':list_Symbol, 'NATR':list_NATR, 'VolRatio':list_VolRatio, 'VolUSD_SMA':list_VolUSD_SMA})
        df_screened["NATR"]       = df_screened["NATR"].apply(pd.to_numeric, errors='coerce')
        df_screened["VolRatio"]   = df_screened["VolRatio"].apply(pd.to_numeric, errors='coerce')
        df_screened["VolUSD_SMA"] = df_screened["VolUSD_SMA"].apply(pd.to_numeric, errors='coerce')
        df_screened = df_screened.sort_values(by="VolUSD_SMA", ascending=False)
        
        df_screened = df_screened.dropna()
        #_________________________________________________________________________

        #df_screened = df_screened.drop(df_screened.loc[df_screened['VolRatio']<0].index)

        len_list_Symbol = len(list_Symbol)

        step = 0.2
        for drop_NATR in np.arange(0 , 100 , step):
            drop_NATR_df = df_screened.drop(df_screened.loc[df_screened['NATR'] < drop_NATR].index)
            len_drop_NATR = len(drop_NATR_df['Ticker'].tolist())
            
            criteria = 20 # %

            if len_drop_NATR < int(len_list_Symbol*(criteria*0.01)) :
                drop_NATR = drop_NATR - step
                break

        step = 10000
        for drop_VolUSD in np.arange(0 , 999999999999 , step):
            VolUSD_SMA_df = df_screened.drop(df_screened.loc[df_screened['VolUSD_SMA'] < drop_VolUSD].index)
            len_VolUSD_SMA = len(VolUSD_SMA_df['Ticker'].tolist())

            criteria = 20 # %

            if len_VolUSD_SMA < int(len_list_Symbol*(criteria*0.01)) :
                drop_VolUSD = drop_VolUSD - step
                break

        # TOP 50% of NATR & Volume
        df_screened = df_screened.drop(df_screened.loc[df_screened['NATR'] < drop_NATR].index)
        df_screened = df_screened.drop(df_screened.loc[df_screened['VolUSD_SMA'] < drop_VolUSD].index)
        df_screened.reset_index(drop=True, inplace=True)

        list_Symbol = df_screened['Ticker'].tolist()

        len_list_Symbol = len(list_Symbol)

        print("passed screened ↓")
        print(f"Screened Symbol Count -> {len_list_Symbol}")

        print(df_screened)
        
        #---------------------------------------- UPLOAD ----------------------------------------------------------
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"./config/GCP_marketstar.json"
        
        client_storage = storage.Client()
        
        bucket_name = "bankof3v_bucket"
        
        bucket = client_storage.get_bucket(bucket_name)

        GCS_path = f'SCREEN/{ActivationTime}.csv'
        LOCAL_path = f'{working_dir}/static/{GCS_path}'
        
        df_screened.to_csv(LOCAL_path, index=False)
        
        blob_data = bucket.blob(GCS_path)
        
        blob_data.upload_from_filename(LOCAL_path)
        
        logging.info(f"Successfuly Uploaded Screener Result -> {LOCAL_path}")
        discorder.send("Screen SUCCESS", 
            f"{ActivationTime}",
            f"{len_list_Symbol} symbols -> {list_Symbol}", 
            username = vm.GCP_instance,
            server = discord_server)

    return list_Symbol

#____________________________________________________________________________________-

def kline(Ticker, days, KLINE_INTERVAL):

    client = Client(pw.binance_api_key, pw.binance_api_secret)

    kline_data = client.futures_historical_klines(Ticker, KLINE_INTERVAL,  f"{days} day ago UTC")

    df = pd.DataFrame(kline_data, columns = ['OpenTime','Open','High','Low','Close','Volume','CloseTime','VolumeUSD','Trades','TakerBuyVolume','TakerBuyVolumeUSD','Ignore'])

    df['OpenTime'] = df['OpenTime']/1000
    df['CloseTime'] = df['CloseTime']/1000

    # df['OpenTime'] = pd.to_datetime(df['OpenTime'].astype(int), unit='s')
    # df['CloseTime'] = pd.to_datetime(df['CloseTime'].astype(int), unit='s')

    df["Open"]   = df["Open"].apply(lambda x: float(x))
    df["High"]   = df["High"].apply(lambda x: float(x))
    df["Low"]    = df["Low"].apply(lambda x: float(x))
    df["Close"]  = df["Close"].apply(lambda x: float(x))
    df["Volume"] = df["Volume"].apply(lambda x: float(x))
    df["Trades"] = df["Trades"].apply(lambda x: float(x))
    df["VolumeUSD"] = df["VolumeUSD"].apply(lambda x: float(x))
    df["TakerBuyVolumeUSD"] = df["TakerBuyVolumeUSD"].apply(lambda x: float(x))
    df["TakerBuyVolume"] = df["TakerBuyVolume"].apply(lambda x: float(x))
    df["Ignore"] = df["Ignore"].apply(lambda x: float(x))

    logging.info(f"Created History Database of {Ticker} for {days} by {KLINE_INTERVAL} timeframe")

    return df

#------------------------------------------------------------
if __name__ == "__main__":

    df = kline("BTCUSDT", 14, Client.KLINE_INTERVAL_1HOUR)
    print(df)

# Base means Coin
# taker_buy_base_asset_volume = maker_sell_base_asset_volume
# taker_sell_base_asset_volume = maker_buy_base_asset_volume
# total_volume = taker_buy_base_asset_volume + taker_sell_base_asset_volume
# total_volume = maker_buy_base_asset_volume + maker_sell_base_asset_volume

# Quote means USDT
# taker_buy_Quote_asset_volume = maker_sell_Quote_asset_volume
# taker_sell_Quote_asset_volume = maker_buy_Quote_asset_volume
# total_volume = taker_buy_Quote_asset_volume + taker_sell_Quote_asset_volume
# total_volume = maker_buy_Quote_asset_volume + maker_sell_Quote_asset_volume