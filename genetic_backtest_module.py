# Genetic Backtest Algorithm
import sys, pathlib, time, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import module, selection, calc
import pandas as pd
from strategy.Kan import Kan_backtest
from strategy.Rsix import Rsi_backtest
from google.cloud import storage

#-------------------------------------------------------------------------------

def create_chunk_kline(df_kline_days, chunk_index, days, TimeFrame):

    BT_start_index = int(chunk_index*days*int(1440/TimeFrame))
    BT_end_index = int((chunk_index+1)*days*int(1440/TimeFrame))

    TR_start_index = int((chunk_index+1)*(days*int(1440/TimeFrame)))
    TR_end_index = int((chunk_index+2)*(days*int(1440/TimeFrame)))

    backtest_kline_chunk = df_kline_days.iloc[BT_start_index : BT_end_index]
    testrun_kline_chunk = df_kline_days.iloc[TR_start_index : TR_end_index]

    print(f"backtest chunk -> {BT_start_index}:{BT_end_index} in {len(df_kline_days)}")
    print(f"testrun chunk -> {TR_start_index}:{TR_end_index} in {len(df_kline_days)}")

    backtest_kline_chunk.reset_index(drop=True, inplace=True)
    testrun_kline_chunk.reset_index(drop=True, inplace=True)

    return backtest_kline_chunk, testrun_kline_chunk

#-------------------------------------------------------------------------------

def backTest(df_kline_chunk_4_backtest, df_backtest_all, TimeFrame,Strategy, Symbol, core, debug, days, chunk_div_size, chunk_index, side):

    if Strategy == "KanL" or Strategy == "KanS":
        backtest_result = Kan_backtest.batch(core, side, df_kline_chunk_4_backtest, TimeFrame, debug)
    else:
        print("Error. Strategy for Genetic Backtest is not ready...")

    df_backtest_chunk = module.create_df_backtest(backtest_result)

    df_backtest_chunk = calc.backtest_result(df_kline_chunk_4_backtest,df_backtest_chunk,Symbol,TimeFrame,Strategy,days,"job",chunk_div_size,chunk_index)

    df_backtest_all = pd.concat([df_backtest_all, df_backtest_chunk])

    # df_backtest_all.to_csv("backtest.csv")

    return df_backtest_all, df_backtest_chunk

#-------------------------------------------------------------------------------

def testrun(df_backtest_chunk,df_kline_chunk_4_testrun, TimeFrame, Strategy, Symbol, days, chunk_div_size, chunk_index,df_testrun_all, df_survived_all,df_elite_all, side):

        df_survived_all, df_elite_all, list_params, result_type = \
        selection.run(df_survived_all, df_elite_all, df_backtest_chunk)

        if Strategy == "KanL" or Strategy == "KanS":
            unfinished_profit, list_Profit, list_paperProfitMAX, list_paperLossMAX, EntryTimes, ExitTimes = \
            Kan_backtest.run(df_kline_chunk_4_testrun, TimeFrame, side, list_params[0], list_params[1], list_params[2], list_params[3])

        df_testrun_chunk = module.create_df_backtest([[list_params, unfinished_profit, list_Profit, \
                                                        list_paperProfitMAX, list_paperLossMAX, EntryTimes, ExitTimes]])

        df_testrun_chunk = calc.backtest_result(df_kline_chunk_4_testrun,df_testrun_chunk,Symbol,TimeFrame,Strategy,days,result_type, chunk_div_size,chunk_index)

        df_testrun_all = pd.concat([df_testrun_all, df_testrun_chunk])

        # print(f"testrun done. {Strategy} {Symbol} {list_params}")

        return df_survived_all, df_elite_all, df_testrun_all

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
#_______________________________________________________________________________
#
def export_df(ActivationTime, debug, df_backtest_all, df_survived_all,df_elite_all,df_testrun_all):

    df_backtest_all.reset_index(drop=True, inplace=True)
    df_survived_all.reset_index(drop=False, inplace=True)
    df_elite_all.reset_index(drop=False, inplace=True)
    df_testrun_all.reset_index(drop=False, inplace=True)

    if debug == True:
        debug_dir = "DEBUG"

    os.makedirs(f"static/{debug_dir}/{ActivationTime}", exist_ok=True)

    df_backtest_all.to_csv(f"static/{debug_dir}/{ActivationTime}/backtest.csv")
    df_survived_all.to_csv(f"static/{debug_dir}/{ActivationTime}/servived.csv")
    df_elite_all.to_csv(f"static/{debug_dir}/{ActivationTime}/elite.csv")
    df_testrun_all.to_csv(f"static/{debug_dir}/{ActivationTime}/testrun.csv")

    client_storage = storage.Client()
    bucket_name    = "bankof3v_bucket"
    bucket         = client_storage.get_bucket(bucket_name)

    GCS_path_backtest = f'{debug_dir}/{ActivationTime}/backtest.csv'
    GCS_path_servived = f'{debug_dir}/{ActivationTime}/servived.csv'
    GCS_path_elite = f'{debug_dir}/{ActivationTime}/elite.csv'
    GCS_path_testrun = f'{debug_dir}/{ActivationTime}/testrun.csv'

    LOCAL_path_backtest = f'{working_dir}/static/{GCS_path_backtest}'
    LOCAL_path_servived = f'{working_dir}/static/{GCS_path_servived}'
    LOCAL_path_elite = f'{working_dir}/static/{GCS_path_elite}'
    LOCAL_path_testrun = f'{working_dir}/static/{GCS_path_testrun}'

    blob_backtest_all = bucket.blob(GCS_path_backtest)
    blob_survived_all = bucket.blob(GCS_path_servived)
    blob_elite_all   = bucket.blob(GCS_path_elite)
    blob_testrun_all = bucket.blob(GCS_path_testrun)

    blob_backtest_all.upload_from_filename(LOCAL_path_backtest) 
    blob_survived_all.upload_from_filename(LOCAL_path_servived) 
    blob_elite_all.upload_from_filename(LOCAL_path_elite) 
    blob_testrun_all.upload_from_filename(LOCAL_path_testrun) 

