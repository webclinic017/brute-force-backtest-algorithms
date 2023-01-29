import sys, pathlib, os, logging
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
sys.path.append(f"{str(working_dir)}/config")
import pandas as pd
from binance.enums import *
import pandas as pd
import numpy as np
from operator import sub

#________________________________________________________________________________
def testrun_performance(df_elite_all, df_testrun_all):

    df_testrun_all["SCORE_TIME_EFFICIENCY"] = np.where(df_elite_all["TIME_EFFICIENCY"] == df_testrun_all["TIME_EFFICIENCY"],
                                            0,
                                            round((df_testrun_all["TIME_EFFICIENCY"]/df_elite_all["TIME_EFFICIENCY"])*100,2))

    return df_testrun_all

#________________________________________________________________________________

def backtest_result(df_kline_chunk, 
                    df_backtest_result, 
                    Symbol, 
                    TimeFrame,
                    Strategy, 
                    days, 
                    result_type, 
                    chunk_div_size = 0, 
                    chunk_index = 0):

    series_sample_size = []
    series_best = []
    series_worst = []
    series_holdSec = []
    series_holdHour = []
    series_total_holdHour = []
    series_time_efficiency = []
    series_average_holdHour = []
    series_max_holdHour = []
    series_min_holdHour = []
    series_win_holdHour = []
    series_lose_holdHour = []
    series_win_average_hour = []
    series_lose_average_hour = []
    series_winRatio = []
    series_gain_size = []
    series_gain_progress = []
    series_gain_sum = []
    series_unfinished_gain = []
    series_netp_ave = []
    series_netp_ave_win = []
    series_netp_ave_lose = []
    series_paper_loss_max = []
    series_paper_loss_ave = []

    for index, row in df_backtest_result.iterrows():

        series_sample_size.append(len(row["NET_PROFIT_SERIES"]))

        series_best.append(max(row["NET_PROFIT_SERIES"],default=None))
        series_worst.append(min(row["NET_PROFIT_SERIES"],default=None))

        series_paper_loss_max.append(min(row["PAPER_LOSS_SERIES"],default=None))

        series_holdSec.append(list(map(int, map(sub, row["EXIT_TIME_SERIES"], row["ENTRY_TIME_SERIES"]))))

        for sec_holdtime in series_holdSec:
            list_hour_holdtime = (list(map(lambda x:round(x/(60*60),1), sec_holdtime)))

            # 1, Hold time hourly average. 
            average_holdHour = round(np.mean(list_hour_holdtime),2)
            total_holdHour = sum(list_hour_holdtime)

            # 2, Max Min hold time. 
            max_holdHour = 0 if len(list_hour_holdtime) == 0 else max(list_hour_holdtime)
            min_holdHour =  0 if len(list_hour_holdtime) == 0 else min(list_hour_holdtime)

            # 3, Winning Losing average hold time. 
            list_win_holdHour = [hour_holdtime for hour_holdtime, net_profit in zip(list_hour_holdtime, row["NET_PROFIT_SERIES"]) if net_profit > 0]
            list_lose_holdHour = [hour_holdtime for hour_holdtime, net_profit in zip(list_hour_holdtime, row["NET_PROFIT_SERIES"]) if net_profit <= 0]

        series_holdHour.append(list_hour_holdtime)
        series_total_holdHour.append(round(total_holdHour,2))
        series_average_holdHour.append(average_holdHour)
        series_max_holdHour.append(max_holdHour)
        series_min_holdHour.append(min_holdHour)
        series_win_holdHour.append(list_win_holdHour)
        series_lose_holdHour.append(list_lose_holdHour)
        series_win_average_hour.append(round(np.mean([win_holdHour for win_holdHour in list_win_holdHour]),2))
        series_lose_average_hour.append(round(np.mean([lose_holdHour for lose_holdHour in list_lose_holdHour]),2))

        wins = len([NET_PROFIT_SERIES for NET_PROFIT_SERIES in row["NET_PROFIT_SERIES"] if NET_PROFIT_SERIES >= 0])

        series_winRatio.append(0 if wins==0 else round((wins/len(row["NET_PROFIT_SERIES"]))*100,1))

        list_gain_progress = []
        list_gain_size = []
        initial_asset = 100
        gain_progress = initial_asset

        for NETP in row["NET_PROFIT_SERIES"]:
            gain_progress_last = gain_progress # DONT REMOVE. difference between now and last
            gain_progress = round((gain_progress*(NETP/initial_asset))+gain_progress,2)
            list_gain_progress.append(gain_progress)
            list_gain_size.append(round(gain_progress - gain_progress_last,2))

        series_gain_size.append(list_gain_size)

        series_gain_progress.append(list_gain_progress)
        series_gain_sum.append(list_gain_progress[-1] if len(list_gain_progress)>0 else 100)
        series_unfinished_gain.append(round(row["UNFINISHED_PROFIT"]*(series_gain_sum[-1]/100),2))

        netp_ave = np.mean(row["NET_PROFIT_SERIES"])
        series_netp_ave.append(round(netp_ave,2))

        series_netp_ave_win.append(round(np.mean([NET_PROFIT_SERIES for NET_PROFIT_SERIES in row["NET_PROFIT_SERIES"] if NET_PROFIT_SERIES >= 0]),2))
        series_netp_ave_lose.append(round(np.mean([NET_PROFIT_SERIES for NET_PROFIT_SERIES in row["NET_PROFIT_SERIES"] if NET_PROFIT_SERIES < 0]),2))
        series_paper_loss_ave.append(round(np.mean([PAPER_LOSS_SERIES for PAPER_LOSS_SERIES in row["PAPER_LOSS_SERIES"]]),2))

        series_time_efficiency.append(0 if total_holdHour == 0 else round((netp_ave / average_holdHour)*100,2))
    try:
        df_backtest_result['START'] = pd.to_datetime(df_kline_chunk.iloc[0,0].astype(int), unit='s')
        df_backtest_result["END"] = pd.to_datetime(df_kline_chunk.iloc[-1,0].astype(int), unit='s')
    except:
        df_backtest_result['START'] = None
        df_backtest_result['END'] = None

    df_backtest_result["SAMPLE_SIZE"]         = series_sample_size
    df_backtest_result["BEST_TRADE"]          = series_best
    df_backtest_result["WORST_TRADE"]         = series_worst
    # df_backtest_result["HOLD_SEC_SERIES"]     = series_holdSec
    df_backtest_result["HOLD_HOUR_SERIES"]    = series_holdHour
    df_backtest_result["HOUR_AVE"]            = series_average_holdHour
    df_backtest_result["HOUR_TOTAL"]          = series_total_holdHour
    df_backtest_result["HOUR_MAX"]            = series_max_holdHour
    df_backtest_result["HOUR_MIN"]            = series_min_holdHour
    df_backtest_result["HOUR_WIN_SERIES"]     = series_win_holdHour
    df_backtest_result["HOUR_LOSE_SERIES"]    = series_lose_holdHour
    df_backtest_result["HOUR_WIN_AVE"]        = series_win_average_hour
    df_backtest_result["HOUR_LOSE_AVE"]       = series_lose_average_hour
    df_backtest_result["WIN_RATIO"]           = series_winRatio
    df_backtest_result["GAIN_SIZE_SERIES"]    = series_gain_size
    df_backtest_result["GAIN_PROGRESS_SERIES"]= series_gain_progress
    df_backtest_result["GAIN_SUM"]            = series_gain_sum
    df_backtest_result["NETP_AVE"]            = series_netp_ave
    df_backtest_result["NETP_AVE_WIN"]        = series_netp_ave_win
    df_backtest_result["NETP_AVE_LOSE"]       = series_netp_ave_lose
    df_backtest_result["PAPER_LOSS_MAX"]      = series_paper_loss_max
    df_backtest_result["PAPER_LOSS_AVE"]      = series_paper_loss_ave
    df_backtest_result["UNFINISHED_GAIN"]     = series_unfinished_gain
    df_backtest_result["SYMBOL"]              = Symbol
    df_backtest_result["STRATEGY"]            = Strategy
    df_backtest_result["CHUNK_INDEX"]         = chunk_index +1
    df_backtest_result["DIV_SIZE"]            = chunk_div_size
    df_backtest_result["DAYS_TOTAL"]          = days*chunk_div_size
    df_backtest_result["DAYS_CHUNK"]          = days
    df_backtest_result['TYPE']                = result_type    
    df_backtest_result["TIME_EFFICIENCY"]     = series_time_efficiency
    df_backtest_result["TIMEFRAME"]           = TimeFrame

    df_backtest_result = df_backtest_result[[\
        "STRATEGY",\
        "SYMBOL",\
        "TIMEFRAME",\
        "CHUNK_INDEX",\
        "PARAMS_SERIES",\
        "TYPE",\
        "TIME_EFFICIENCY",\
        "SAMPLE_SIZE",\
        "WIN_RATIO",\
        "GAIN_SUM",\
        "UNFINISHED_PROFIT",\
        "UNFINISHED_GAIN",\
        "NETP_AVE",\
        "NETP_AVE_WIN",\
        "NETP_AVE_LOSE",\
        "HOUR_AVE",\
        "HOUR_TOTAL",\
        "HOUR_MAX",\
        "HOUR_MIN",\
        "HOUR_WIN_AVE",\
        "HOUR_LOSE_AVE",\
        "BEST_TRADE",\
        "WORST_TRADE",\
        "PAPER_LOSS_MAX",\
        "PAPER_LOSS_AVE",\
        "DIV_SIZE",\
        "DAYS_TOTAL",\
        "DAYS_CHUNK",\
        "START",\
        "END",\
        "NET_PROFIT_SERIES",\
        "PAPER_LOSS_SERIES",\
        "HOLD_HOUR_SERIES",\
        "HOUR_WIN_SERIES",\
        "HOUR_LOSE_SERIES",\
        "GAIN_SIZE_SERIES",\
        "GAIN_PROGRESS_SERIES",\
        "ENTRY_TIME_SERIES",\
        "EXIT_TIME_SERIES",\
        ]]

    return df_backtest_result