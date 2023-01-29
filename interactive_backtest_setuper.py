import sys, pathlib, os
outside_dir = pathlib.Path(__file__).resolve().parent.parent.parent 
working_dir = pathlib.Path(__file__).resolve().parent.parent 
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(working_dir))
sys.path.append(f"{str(working_dir)}/config")
import inquirer, logging, datetime, time
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

    # ActivationTime
    ActivationTime = datetime.datetime.now().strftime('%y%m%d%H%M')

    # debug_questions
    debug_questions  = [inquirer.List('debug', message="Debug?", choices=[True,False],),]
    debug_answers    = inquirer.prompt(debug_questions)
    debug            = debug_answers["debug"]

    # Strategy_questions
    Strategy_questions = [
        inquirer.Checkbox(
            "list_Strategies",
            message="Which Strategies do you wanna backtest?",
            choices=["KanL","KanS","DeviL", "DeviS", "RsiL", "RsiS"]),]
    list_Strategies = inquirer.prompt(Strategy_questions, theme=WorkplaceFriendlyTheme())
    list_Strategies = list_Strategies["list_Strategies"]

    # # # # debug auto fill # # # 
    if debug == True:
        Platform = "LOCAL"
        core = int(os.cpu_count()/2)
        list_chunk_days = [4]
        chunk_div_size  = 3
    # # # # # # # # # # # # # # # 

    else:
        # Platform_questions
        Platform_questions  = [inquirer.List('Platform', message="Which Platform?", choices=["LOCAL",'GCP', 'Azure', "AWS"],),]
        Platform_answers    = inquirer.prompt(Platform_questions)
        Platform            = Platform_answers["Platform"]

        # core_questions
        CPUs = os.cpu_count()
        CPUsHalf = int(CPUs/2)
        CPUsHalfHalf = int(CPUsHalf/2)

        # core_questions
        core_questions  = [inquirer.List('core', message="How many workers?", choices=[CPUsHalf, CPUs],),]
        core_answers    = inquirer.prompt(core_questions)
        core            = core_answers["core"]

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
    if Platform == "GCP":
        project,zone,instance= vm.GCP_project,vm.GCP_zone,vm.GCP_instance
    elif Platform == "AWS":
        instance = vm.AWS_instance
    elif Platform == "Azure":
        project,zone,instance= "?","?","?"
    elif Platform == "LOCAL":
        project,zone,instance="?","?","?"

    # Discord server
    if debug == True:
        discord_server = "backtest_debug"
    else:
        discord_server = "backtest"

    # confirm_questions
    confirm_questions = [inquirer.List('confirm', 
                message=f"confirm={debug},\
                        Platform={Platform}:{instance},\
                        cores={core},\
                        list_chunk_days={list_chunk_days},\
                        chunk_div_size={chunk_div_size},\
                        list_Strategies={list_Strategies}",\
                        choices=["No. Quit", "Yes"],),]
    confirm_answers = inquirer.prompt(confirm_questions)
    confirm         = confirm_answers["confirm"]

    # timer
    if confirm == "Yes":
        timer_global = time.time()
        
        return ActivationTime, timer_global, debug, Platform, core, list_chunk_days, chunk_div_size, list_Strategies, discord_server
    else:
        quit()


# test run
if __name__ == "__main__": 

    setup_data = run()

    from pprint import pprint 

    pprint(setup_data)

