import sys, pathlib, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
sys.path.append(f"{str(working_dir)}/config")
import inquirer, logging, datetime, time_data
from inquirer.themes import Default
from tools import vm

sys.path.append(os.path.realpath("."))

class WorkplaceFriendlyTheme(Default):
    """Custom theme replacing X with Y and o with N"""

    def __init__(self):
        super().__init__()
        self.Checkbox.selected_icon = "Y"
        self.Checkbox.unselected_icon = "N"

def run():
    logging.basicConfig(level=logging.INFO,format="%(asctime)s : %(message)s")

    # activationTime
    activationTime = datetime.datetime.now().strftime('%y%m%d%H%M')

    # debug_questions
    debug_questions  = [inquirer.List('debug', message="Debug?", choices=[True,False],),]
    debug_answers    = inquirer.prompt(debug_questions)
    debug            = debug_answers["debug"]

    # strategy_questions
    strategy_questions = [
        inquirer.Checkbox(
            "list_strategies",
            message="Which Strategies do you wanna backtest?",
            choices=["KanL","KanS","DeviL", "DeviS", "RsiL", "RsiS"]),]
    list_strategies = inquirer.prompt(strategy_questions, theme=WorkplaceFriendlyTheme())
    list_strategies = list_strategies["list_strategies"]

    # # # # debug auto fill # # # 
    if debug == True:
        platform = "LOCAL"
        coreLine = int(os.cpu_count()/2)
        list_chunk_days = [4]
        chunk_div_size  = 3
    # # # # # # # # # # # # # # # 

    else:
        # platform_questions
        platform_questions  = [inquirer.List('platform', message="Which platform?", choices=["LOCAL",'googleCloud', 'Azure', "aws"],),]
        platform_answers    = inquirer.prompt(platform_questions)
        platform            = platform_answers["platform"]

        # coreLine_questions
        coreLine_numbers = os.cpu_count()
        coreLine_numbersHalf = int(coreLine_numbers/2)
        coreLine_numbersHalfHalf = int(coreLine_numbersHalf/2)

        # coreLine_questions
        coreLine_questions  = [inquirer.List('coreLine', message="How many workers?", choices=[coreLine_numbersHalf, coreLine_numbers],),]
        coreLine_answers    = inquirer.prompt(coreLine_questions)
        coreLine            = coreLine_answers["coreLine"]

        # chunk_days_questions
        chunk_days_questions = [
            inquirer.Checkbox(
                "list_chunk_days",
                message="How many chunk_days do you want?",
                choices=[4,7,10,14]),]
        list_chunk_days = inquirer.prompt(chunk_days_questions, theme=WorkplaceFriendlyTheme())
        list_chunk_days = list_chunk_days["list_chunk_days"]

        # chunk_div_size_questions
        chunk_div_size_questions  = [inquirer.List('chunk_div_size', message="How many chunk_div_size?", choices=[3,4,5,6,7],),]
        chunk_div_size_answers    = inquirer.prompt(chunk_div_size_questions)
        chunk_div_size            = chunk_div_size_answers["chunk_div_size"]

    # cloud compute instance
    if platform == "googleCloud":
        project,zone,instance= vm.googleCloud_project,vm.googleCloud_zone,vm.googleCloud_instance
    elif platform == "aws":
        instance = vm.aws_instance
    elif platform == "Azure":
        project,zone,instance= "?","?","?"
    elif platform == "LOCAL":
        project,zone,instance="?","?","?"

    # Discord server
    if debug == True:
        discord_server = "backtest_debug"
    else:
        discord_server = "backtest"

    # confirm_questions
    confirm_questions = [inquirer.List('confirm', 
                message=f"confirm={debug},\
                        platform={platform}:{instance},\
                        coreLines={coreLine},\
                        list_chunk_days={list_chunk_days},\
                        chunk_div_size={chunk_div_size},\
                        list_strategies={list_strategies}",\
                        choices=["No. Quit", "Yes"],),]
    confirm_answers = inquirer.prompt(confirm_questions)
    confirm         = confirm_answers["confirm"]

    # timer
    if confirm == "Yes":
        timer_global = time_data.time_data()
        
        return activationTime, timer_global, debug, platform, coreLine, list_chunk_days, chunk_div_size, list_strategies, discord_server
    else:
        quit()


# test run
if __name__ == "__main__": 

    setup_data = run()

    from pprint import pprint 

    pprint(setup_data)

