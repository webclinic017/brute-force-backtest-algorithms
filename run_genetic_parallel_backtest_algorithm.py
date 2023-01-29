# Genetic Backtest Algorithm
import sys, pathlib, time, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import setup, calc, module, screener
from tools import report
from tqdm import tqdm
import pandas as pd
from pprint import pprint
import gen_module as gen
from tools import discorder as discord, vm

def run(list_Symbols, ActivationTime, timer_global, debug, Platform, core, list_chunk_days, chunk_div_size, list_Strategies, discord_server):

    list_TimeFrame  = [1]

    df_backtest_all = pd.DataFrame()
    df_survived_all = pd.DataFrame()
    df_elite_all    = pd.DataFrame()
    df_testrun_all  = pd.DataFrame()

    for Symbol in tqdm(list_Symbols):
        print(f"Going to download kline from binance -> {max(list_chunk_days)*chunk_div_size} days")

        # df_kline -> df_klie_copy -> df_kline_days -> df_kline_chunk x 5
        df_kline = module.create_df_kline(Symbol, min(list_TimeFrame), max(list_chunk_days)*chunk_div_size)

        for Strategy in list_Strategies:
            print(f"Strategy -> {Strategy}")

            side = True if list(Strategy)[-1] == "L" else False

            for days in list_chunk_days:
                print(f"days -> {days}")

                for TimeFrame in list_TimeFrame:

                    df_kline_copy = df_kline.copy()

                    df_kline_days = df_kline_copy.iloc[len(df_kline_copy)-(days*int(1440/TimeFrame)*chunk_div_size) : len(df_kline_copy)]
                    df_kline_days.reset_index(drop=True, inplace=True)

                    for chunk_index in range(chunk_div_size):

                        df_kline_chunk_4_backtest, df_kline_chunk_4_testrun = gen.create_chunk_kline(df_kline_days, chunk_index, days, TimeFrame)

                        df_backtest_all, df_backtest_chunk = \
                        gen.backTest(df_kline_chunk_4_backtest, df_backtest_all, TimeFrame,Strategy, Symbol, core, debug, days, chunk_div_size, chunk_index, side)

                        df_survived_all, df_elite_all, df_testrun_all = \
                        gen.testrun(df_backtest_chunk,df_kline_chunk_4_testrun, TimeFrame,Strategy, Symbol, days, chunk_div_size, chunk_index,df_testrun_all, df_survived_all,df_elite_all, side)

                        discord.send(message="running...", server = discord_server)


    df_testrun_all = calc.testrun_performance(df_elite_all, df_testrun_all)

    gen.export_df(ActivationTime, debug, df_backtest_all, df_survived_all,df_elite_all,df_testrun_all)

    discord.send(message="done!", server = discord_server)

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"{working_dir}/config/GCP_marketstar.json"

    ActivationTime, timer_global, debug, Platform, core, list_chunk_days, chunk_div_size, list_Strategies, discord_server  = setup.run()
    
    try:

        list_Symbols = screener.run(debug, ActivationTime, discord_server)

        run(list_Symbols, ActivationTime, timer_global, debug, Platform, core, list_chunk_days, chunk_div_size, list_Strategies, discord_server)

        vm.GCP_stop(Platform, vm.GCP_project,vm.GCP_zone,vm.GCP_instance)

    except Exception as e:

        discord.send(message=f"Backtest ERROR! {e}", server = "backtest_error")

        vm.GCP_stop(Platform, vm.GCP_project,vm.GCP_zone,vm.GCP_instance)


