# Genetic Backtest Algorithm
import sys, pathlib, time_data, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import module, selection, calc
import pandas as pd
from strategy.Kan import kanBacktest
from strategy.Rsix import rsiBacktest
from google.cloud import storage

#-------------------------------------------------------------------------------

def create_chunk_kline(df_kline_days, chunk_index, days, timeFrame):

    backtest_start_index = int(chunk_index*days*int(1440/timeFrame))
    backtest_end_index = int((chunk_index+1)*days*int(1440/timeFrame))

    testRun_start_index = int((chunk_index+1)*(days*int(1440/timeFrame)))
    testRun_end_index = int((chunk_index+2)*(days*int(1440/timeFrame)))

    backtest_kline_chunk = df_kline_days.iloc[backtest_start_index : backtest_end_index]
    testrun_kline_chunk = df_kline_days.iloc[testRun_start_index : testRun_end_index]

    print(f"backtest chunk -> {backtest_start_index}:{backtest_end_index} in {len(df_kline_days)}")
    print(f"testrun chunk -> {testRun_start_index}:{testRun_end_index} in {len(df_kline_days)}")

    backtest_kline_chunk.reset_index(drop=True, inplace=True)
    testrun_kline_chunk.reset_index(drop=True, inplace=True)

    return backtest_kline_chunk, testrun_kline_chunk

#-------------------------------------------------------------------------------

def backTest(df_kline_chunk_4_backtest, df_backtest_all, timeFrame,strategy, symbol, coreLine, debug, days, chunk_div_size, chunk_index, side):

    if strategy == "KanL" or strategy == "KanS":
        backtest_result = kanBacktest.batch(coreLine, side, df_kline_chunk_4_backtest, timeFrame, debug)
    else:
        print("Error. strategy for Genetic Backtest is not ready...")

    df_backtest_chunk = module.create_df_backtest(backtest_result)

    df_backtest_chunk = calc.backtest_result(df_kline_chunk_4_backtest,df_backtest_chunk,symbol,timeFrame,strategy,days,"job",chunk_div_size,chunk_index)

    df_backtest_all = pd.concat([df_backtest_all, df_backtest_chunk])

    # df_backtest_all.to_csv("backtest.csv")

    return df_backtest_all, df_backtest_chunk

#-------------------------------------------------------------------------------

def testrun(df_backtest_chunk,df_kline_chunk_4_testrun, timeFrame, strategy, symbol, days, chunk_div_size, chunk_index,df_testrun_all, df_survived_all,df_elite_all, side):

        df_survived_all, df_elite_all, list_params, result_type = \
        selection.run(df_survived_all, df_elite_all, df_backtest_chunk)

        if strategy == "KanL" or strategy == "KanS":
            unfinishedProfit, list_profit, list_paperprofitMAX, list_paperLossMAX, entryTimes, exitTimes = \
            kanBacktest.run(df_kline_chunk_4_testrun, timeFrame, side, list_params[0], list_params[1], list_params[2], list_params[3])

        df_testrun_chunk = module.create_df_backtest([[list_params, unfinishedProfit, list_profit, \
                                                        list_paperprofitMAX, list_paperLossMAX, entryTimes, exitTimes]])

        df_testrun_chunk = calc.backtest_result(df_kline_chunk_4_testrun,df_testrun_chunk,symbol,timeFrame,strategy,days,result_type, chunk_div_size,chunk_index)

        df_testrun_all = pd.concat([df_testrun_all, df_testrun_chunk])

        # print(f"testrun done. {strategy} {symbol} {list_params}")

        return df_survived_all, df_elite_all, df_testrun_all

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
#_______________________________________________________________________________
#
def export_df(activationTime, debug, df_backtest_all, df_survived_all,df_elite_all,df_testrun_all):

    df_backtest_all.reset_index(drop=True, inplace=True)
    df_survived_all.reset_index(drop=False, inplace=True)
    df_elite_all.reset_index(drop=False, inplace=True)
    df_testrun_all.reset_index(drop=False, inplace=True)

    if debug == True:
        debug_dir = "DEBUG"

    os.makedirs(f"static/{debug_dir}/{activationTime}", exist_ok=True)

    df_backtest_all.to_csv(f"static/{debug_dir}/{activationTime}/backtest.csv")
    df_survived_all.to_csv(f"static/{debug_dir}/{activationTime}/servived.csv")
    df_elite_all.to_csv(f"static/{debug_dir}/{activationTime}/elite.csv")
    df_testrun_all.to_csv(f"static/{debug_dir}/{activationTime}/testrun.csv")

    client_storage = storage.Client()
    bucket_name    = "project_bucket"
    bucket         = client_storage.get_bucket(bucket_name)

    googleCloudStorage_path_backtest = f'{debug_dir}/{activationTime}/backtest.csv'
    googleCloudStorage_path_servived = f'{debug_dir}/{activationTime}/servived.csv'
    googleCloudStorage_path_elite = f'{debug_dir}/{activationTime}/elite.csv'
    googleCloudStorage_path_testrun = f'{debug_dir}/{activationTime}/testrun.csv'

    local_path_backtest = f'{working_dir}/static/{googleCloudStorage_path_backtest}'
    local_path_servived = f'{working_dir}/static/{googleCloudStorage_path_servived}'
    local_path_elite = f'{working_dir}/static/{googleCloudStorage_path_elite}'
    local_path_testrun = f'{working_dir}/static/{googleCloudStorage_path_testrun}'

    blob_backtest_all = bucket.blob(googleCloudStorage_path_backtest)
    blob_survived_all = bucket.blob(googleCloudStorage_path_servived)
    blob_elite_all   = bucket.blob(googleCloudStorage_path_elite)
    blob_testrun_all = bucket.blob(googleCloudStorage_path_testrun)

    blob_backtest_all.upload_from_filename(local_path_backtest) 
    blob_survived_all.upload_from_filename(local_path_servived) 
    blob_elite_all.upload_from_filename(local_path_elite) 
    blob_testrun_all.upload_from_filename(local_path_testrun) 

