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
    
    df["highestRange"] = df["high"].rolling(input_TR_length).max()
    df["lowestRange"]  = df["low"].rolling(input_TR_length).min()
    df["normATR"]         = ta.normATR(df[f"highestRange"], df[f"lowestRange"], df["close"].shift(1), length=input_ATR_length)
    df["Rapid_Vol"]    = ta.sma(df["VolumeUSD"], length = input_Vol_Rapid)
    df["Slow_Vol"]     = ta.sma(df["VolumeUSD"], length = input_Vol_Slow)
    df["VolRatio"]     = ((df["Rapid_Vol"]/df["Slow_Vol"])*100)-100
    df["VolUSD_SMA"]    = ta.sma(df["VolumeUSD"], length = input_VolumeUSD)

    return df

#--------------------------------------------------------------------------------

def run(debug, activationTime, discord_server):

    if debug == True:
        list_symbol = ["BTCUSDT", "ETHUSDT"]
        df_screened = pd.DataFrame({'tickerSymbol':list_symbol, 'normATR':[0,0], 'VolRatio':[0,0], 'VolUSD_SMA':[0,0]})

    else:
        os.makedirs(f"{working_dir}/static/SCREEN/{activationTime}", exist_ok=True)

        list_symbol = binance_data.fetch_all_symbols()

        list_normATR       = []
        list_volumeRatio   = []
        list_VolUSD_SMA = []

        for tickerSymbol in list_symbol:
            try:
                df = kline(tickerSymbol, 33, Client.KLINE_INTERVAL_1HOUR)

                df = create_df(df)

                df.drop(columns=['highestRange','lowestRange','Rapid_Vol','Slow_Vol'], inplace=True)
                df.drop(columns=['closeTime','Ignore'], inplace=True)
                df.dropna(inplace=True)

                value_normATR     = round(df.iloc[-1]["normATR"],2)
                value_VolRatio = round(df.iloc[-1]["VolRatio"],2)
                value_VolUSD_SMA = round(df.iloc[-1]["VolUSD_SMA"],2)

                list_normATR.append(value_normATR)
                list_volumeRatio.append(value_VolRatio)
                list_VolUSD_SMA.append(value_VolUSD_SMA)

            except:
                list_normATR.append("NaN")
                list_volumeRatio.append("NaN")
                list_VolUSD_SMA.append("NaN")
                continue

        df_screened = pd.DataFrame({'tickerSymbol':list_symbol, 'normATR':list_normATR, 'VolRatio':list_volumeRatio, 'VolUSD_SMA':list_VolUSD_SMA})
        df_screened["normATR"]       = df_screened["normATR"].apply(pd.to_numeric, errors='coerce')
        df_screened["VolRatio"]   = df_screened["VolRatio"].apply(pd.to_numeric, errors='coerce')
        df_screened["VolUSD_SMA"] = df_screened["VolUSD_SMA"].apply(pd.to_numeric, errors='coerce')
        df_screened = df_screened.sort_values(by="VolUSD_SMA", ascending=False)
        
        df_screened = df_screened.dropna()
        #_________________________________________________________________________

        #df_screened = df_screened.drop(df_screened.loc[df_screened['VolRatio']<0].index)

        len_list_symbol = len(list_symbol)

        step = 0.2
        for drop_normATR in np.arange(0 , 100 , step):
            drop_normATR_df = df_screened.drop(df_screened.loc[df_screened['normATR'] < drop_normATR].index)
            len_drop_normATR = len(drop_normATR_df['tickerSymbol'].tolist())
            
            criteria = 20 # %

            if len_drop_normATR < int(len_list_symbol*(criteria*0.01)) :
                drop_normATR = drop_normATR - step
                break

        step = 10000
        for drop_volumeInUSD in np.arange(0 , 999999999999 , step):
            VolUSD_SMA_df = df_screened.drop(df_screened.loc[df_screened['VolUSD_SMA'] < drop_volumeInUSD].index)
            len_VolUSD_SMA = len(VolUSD_SMA_df['tickerSymbol'].tolist())

            criteria = 20 # %

            if len_VolUSD_SMA < int(len_list_symbol*(criteria*0.01)) :
                drop_volumeInUSD = drop_volumeInUSD - step
                break

        # TOP 50% of normATR & volume
        df_screened = df_screened.drop(df_screened.loc[df_screened['normATR'] < drop_normATR].index)
        df_screened = df_screened.drop(df_screened.loc[df_screened['VolUSD_SMA'] < drop_volumeInUSD].index)
        df_screened.reset_index(drop=True, inplace=True)

        list_symbol = df_screened['tickerSymbol'].tolist()

        len_list_symbol = len(list_symbol)

        print("passed screened ↓")
        print(f"Screened symbol Count -> {len_list_symbol}")

        print(df_screened)
        
        #---------------------------------------- UPLOAD ----------------------------------------------------------
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"./config/googleCloud_project.json"
        
        client_storage = storage.Client()
        
        bucket_name = "project_bucket"
        
        bucket = client_storage.get_bucket(bucket_name)

        googleCloudStorage_path = f'SCREEN/{activationTime}.csv'
        local_path = f'{working_dir}/static/{googleCloudStorage_path}'
        
        df_screened.to_csv(local_path, index=False)
        
        blob_data = bucket.blob(googleCloudStorage_path)
        
        blob_data.upload_from_filename(local_path)
        
        logging.info(f"Successfully Uploaded Screener Result -> {local_path}")
        discorder.send("Screen SUCCESS", 
            f"{activationTime}",
            f"{len_list_symbol} symbols -> {list_symbol}", 
            username = vm.googleCloud_instance,
            server = discord_server)

    return list_symbol

#____________________________________________________________________________________-

def kline(tickerSymbol, days, KLINE_INTERVAL):

    client = Client(pw.binance_api_key, pw.binance_api_secret)

    kline_data = client.futures_historical_klines(tickerSymbol, KLINE_INTERVAL,  f"{days} day ago UTC")

    df = pd.DataFrame(kline_data, columns = ['openTime','open','high','low','close','volume','closeTime','VolumeUSD','trades','TakerBuyVolume','TakerBuyVolumeUSD','Ignore'])

    df['openTime'] = df['openTime']/1000
    df['closeTime'] = df['closeTime']/1000

    # df['openTime'] = pd.to_datetime(df['openTime'].astype(int), unit='s')
    # df['closeTime'] = pd.to_datetime(df['closeTime'].astype(int), unit='s')

    df["open"]   = df["open"].apply(lambda x: float(x))
    df["high"]   = df["high"].apply(lambda x: float(x))
    df["low"]    = df["low"].apply(lambda x: float(x))
    df["close"]  = df["close"].apply(lambda x: float(x))
    df["volume"] = df["volume"].apply(lambda x: float(x))
    df["trades"] = df["trades"].apply(lambda x: float(x))
    df["VolumeUSD"] = df["VolumeUSD"].apply(lambda x: float(x))
    df["TakerBuyVolumeUSD"] = df["TakerBuyVolumeUSD"].apply(lambda x: float(x))
    df["TakerBuyVolume"] = df["TakerBuyVolume"].apply(lambda x: float(x))
    df["Ignore"] = df["Ignore"].apply(lambda x: float(x))

    logging.info(f"Created History Database of {tickerSymbol} for {days} by {KLINE_INTERVAL} timeFrame")

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