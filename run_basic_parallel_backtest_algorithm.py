import sys, pathlib, time, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import setup, module, parallel, screener
from tools import report, vm

def run(ActivationTime, timer_global, list_Symbols, stage, Platform, Worker, list_Strategies, days, discord_server):

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"{working_dir}/config/GCP_marketstar.json"

    total_backtest_counter = 0
    strategy_counter = 0

    for Strategy in list_Strategies:
        timer_strategy = time.time()

        symbol_counter = 0
        
        for Symbol in list_Symbols:
            timer_symbol = time.time()

            df_kline = module.create_df_origin(Symbol, days)

            if "Devi" in Strategy:
                backtest_result = parallel.param4(Worker, Strategy, df_kline, stage)
            if "Rsi" in Strategy:
                backtest_result = parallel.param3(Worker, Strategy, df_kline, stage)

            df_bt_result = module.create_df_backtest(backtest_result)

            df_bt_result = module.calc_result(df_kline, df_bt_result, Symbol, Strategy, days)

            module.upload_gcs(df_bt_result, stage, Strategy, ActivationTime, Symbol)

            symbol_counter += 1
            total_backtest_counter += 1

            report.backtest("symbol", discord_server, list_Symbols, list_Strategies, timer_symbol, timer_strategy,\
                timer_global, Symbol, Strategy, ActivationTime, symbol_counter, strategy_counter, total_backtest_counter)
        
        strategy_counter += 1
        report.backtest("strategy", discord_server, list_Symbols, list_Strategies, timer_symbol, timer_strategy, timer_global, \
            Symbol, Strategy, ActivationTime, symbol_counter, strategy_counter, total_backtest_counter)

#____________________________________________________________________________________________

if __name__ == "__main__":

    ActivationTime, timer_global, stage, Platform, Worker, list_Strategies, days, discord_server = setup.run()

    try:

        list_Symbols = screener.run(stage, ActivationTime, discord_server)

        run(ActivationTime, timer_global, list_Symbols, stage, Platform, Worker, list_Strategies, days, discord_server)

        vm.GCP_stop(Platform, vm.GCP_project,vm.GCP_zone,vm.GCP_instance)

    except Exception as e:

        report.error("backtest error", e)

        vm.GCP_stop(Platform, vm.GCP_project,vm.GCP_zone,vm.GCP_instance)

        
        
    

