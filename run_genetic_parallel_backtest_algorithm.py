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

def run(list_symbols, activationtime_data, time_datar_global, debug, platform, coreLine, list_chunk_days, chunk_div_size, list_strategies, discord_server):

    list_time_dataFrame  = [1]

    df_backtest_all = pd.DataFrame()
    df_survived_all = pd.DataFrame()
    df_elite_all    = pd.DataFrame()
    df_testrun_all  = pd.DataFrame()

    for symbol in tqdm(list_symbols):
        print(f"Going to download kline from binance -> {max(list_chunk_days)*chunk_div_size} days")

        # df_kline -> df_klie_copy -> df_kline_days -> df_kline_chunk x 5
        df_kline = module.create_df_kline(symbol, min(list_time_dataFrame), max(list_chunk_days)*chunk_div_size)

        for strategy in list_strategies:
            print(f"strategy -> {strategy}")

            side = True if list(strategy)[-1] == "L" else False

            for days in list_chunk_days:
                print(f"days -> {days}")

                for time_dataFrame in list_time_dataFrame:

                    df_kline_copy = df_kline.copy()

                    df_kline_days = df_kline_copy.iloc[len(df_kline_copy)-(days*int(1440/time_dataFrame)*chunk_div_size) : len(df_kline_copy)]
                    df_kline_days.reset_index(drop=True, inplace=True)

                    for chunk_index in range(chunk_div_size):

                        df_kline_chunk_4_backtest, df_kline_chunk_4_testrun = gen.create_chunk_kline(df_kline_days, chunk_index, days, time_dataFrame)

                        df_backtest_all, df_backtest_chunk = \
                        gen.backTest(df_kline_chunk_4_backtest, df_backtest_all, time_dataFrame,strategy, symbol, coreLine, debug, days, chunk_div_size, chunk_index, side)

                        df_survived_all, df_elite_all, df_testrun_all = \
                        gen.testrun(df_backtest_chunk,df_kline_chunk_4_testrun, time_dataFrame,strategy, symbol, days, chunk_div_size, chunk_index,df_testrun_all, df_survived_all,df_elite_all, side)

                        discord.send(message="running...", server = discord_server)


    df_testrun_all = calc.testrun_performance(df_elite_all, df_testrun_all)

    gen.export_df(activationtime_data, debug, df_backtest_all, df_survived_all,df_elite_all,df_testrun_all)

    discord.send(message="done!", server = discord_server)

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"{working_dir}/config/googleCloud_project.json"

    activationtime_data, time_datar_global, debug, platform, coreLine, list_chunk_days, chunk_div_size, list_strategies, discord_server  = setup.run()
    
    try:

        list_symbols = screener.run(debug, activationtime_data, discord_server)

        run(list_symbols, activationtime_data, time_datar_global, debug, platform, coreLine, list_chunk_days, chunk_div_size, list_strategies, discord_server)

        vm.googleCloud_stop(platform, vm.googleCloud_project,vm.googleCloud_zone,vm.googleCloud_instance)

    except Exception as e:

        discord.send(message=f"Backtest ERROR! {e}", server = "backtest_error")

        vm.googleCloud_stop(platform, vm.googleCloud_project,vm.googleCloud_zone,vm.googleCloud_instance)


