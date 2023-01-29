import sys, pathlib, time_data, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import pandas as pd
import numpy as np

def run(df_survived_all, df_elite_all, df_backtest_chunk):

    try:
        df_servived_chunk = df_backtest_chunk.copy()

        print(f"original -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~1~ DROP UNprofitABLE
        df_servived_chunk = df_servived_chunk.loc[df_servived_chunk["SAMPLE_SIZE"] != 0 ]

        print(f"SURVIVER ~1~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~2~ DROP LESS THAN 5 TRADES
        df_servived_chunk = df_servived_chunk.sort_values(by="SAMPLE_SIZE", ascending=False)
        df_servived_chunk = df_servived_chunk.iloc[0:int((len(df_servived_chunk)*0.7))]

        print(f"SURVIVER ~2~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~3~ DROP HUGE UNFIN LOSS
        df_servived_chunk = df_servived_chunk.sort_values(by="UNFINISHED_profit", ascending=False)
        df_servived_chunk = df_servived_chunk.iloc[0:int((len(df_servived_chunk)*0.7))]

        print(f"SURVIVER ~3~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~4~ DROP HUGE HUGE PAPER LOSS RECORD
        df_servived_chunk = df_servived_chunk.sort_values(by="PAPER_LOSS_MAX", ascending=False)
        df_servived_chunk = df_servived_chunk.iloc[0:int((len(df_servived_chunk)*0.7))]

        print(f"SURVIVER ~4~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~5~ SORT BY PAPER_LOSS_MAX and DROP the worst 30%
        df_servived_chunk = df_servived_chunk.sort_values(by="PAPER_LOSS_MAX", ascending=False)
        df_servived_chunk = df_servived_chunk.iloc[0:int((len(df_servived_chunk)*0.7))]

        print(f"SURVIVER ~5~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

        # ~6~ SORT BY NETP_AVE and DROP the worst 30%
        df_servived_chunk = df_servived_chunk.sort_values(by="NETP_AVE", ascending=False)
        df_servived_chunk = df_servived_chunk.iloc[0:int((len(df_servived_chunk)*0.7))]

        print(f"SURVIVER ~6~ -> {len(df_servived_chunk)} out of {len(df_backtest_chunk)}")

    except:

        df_servived_chunk = df_backtest_chunk.copy()
        df_servived_chunk = df_servived_chunk.sort_values(by="NETP_AVE", ascending=False)


    df_survived_all = pd.concat([df_survived_all, df_servived_chunk])

    #---      ---#
    #--- SORT ---#
    #---      ---#

    #--- Find Best param ---#
    df_servived_chunk = df_servived_chunk.sort_values(by="time_data_EFFICIENCY", ascending=False)
    df_servived_chunk.reset_index(drop=True, inplace=True) # DONT REMOVE

    try:
        list_params = df_servived_chunk.loc[0,"PARAMS_SERIES"]
        df_elite_chunk = df_servived_chunk.iloc[[0], :]
    except:
        list_params = [0,0,0,0]

        df_elite_chunk = pd.DataFrame({'PARAMS_SERIES': [list_params], 'time_data_EFFICIENCY': [0]})
    
    result_type = "type_A"
    df_elite_chunk["TYPE"] = result_type

    # df_adopt_chunk.reset_index(drop=True, inplace=True)
    df_elite_all = pd.concat([df_elite_all, df_elite_chunk])

    return df_survived_all, df_elite_all, list_params, result_type