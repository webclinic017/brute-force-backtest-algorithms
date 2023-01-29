import sys, pathlib, time, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
import setup, module, parallel, screener
from tools import report, vm

def run(activationTime, timer_global, list_symbols, stage, platform, worker, list_strategies, days, discord_server):

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"{working_dir}/config/googleCloud_project.json"

    total_backtest_counter = 0
    strategy_counter = 0

    for strategy in list_strategies:
        timer_strategy = time.time()

        symbol_counter = 0
        
        for symbol in list_symbols:
            timer_symbol = time.time()

            df_kline = module.create_df_origin(symbol, days)

            if "Devi" in strategy:
                backtest_result = parallel.param4(worker, strategy, df_kline, stage)
            if "Rsi" in strategy:
                backtest_result = parallel.param3(worker, strategy, df_kline, stage)

            df_bt_result = module.create_df_backtest(backtest_result)

            df_bt_result = module.calc_result(df_kline, df_bt_result, symbol, strategy, days)

            module.upload_googleCloudStorage(df_bt_result, stage, strategy, activationTime, symbol)

            symbol_counter += 1
            total_backtest_counter += 1

            report.backtest("symbol", discord_server, list_symbols, list_strategies, timer_symbol, timer_strategy,\
                timer_global, symbol, strategy, activationTime, symbol_counter, strategy_counter, total_backtest_counter)
        
        strategy_counter += 1
        report.backtest("strategy", discord_server, list_symbols, list_strategies, timer_symbol, timer_strategy, timer_global, \
            symbol, strategy, activationTime, symbol_counter, strategy_counter, total_backtest_counter)

#____________________________________________________________________________________________

if __name__ == "__main__":

    activationTime, timer_global, stage, platform, worker, list_strategies, days, discord_server = setup.run()

    try:

        list_symbols = screener.run(stage, activationTime, discord_server)

        run(activationTime, timer_global, list_symbols, stage, platform, worker, list_strategies, days, discord_server)

        vm.googleCloud_stop(platform, vm.googleCloud_project,vm.googleCloud_zone,vm.googleCloud_instance)

    except Exception as e:

        report.error("backtest error", e)

        vm.googleCloud_stop(platform, vm.googleCloud_project,vm.googleCloud_zone,vm.googleCloud_instance)

        
        
    

