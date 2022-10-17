import os
import requests
import collections 
from collections import OrderedDict
from datetime import datetime
import pytz


API_BASE_URL = os.environ.get("API_BASE_URL", "https://diablo2.io/dclone_api.php")
API_D2RWZ_DC_PROCESS = os.environ.get("API_BASE_URL", "https://d2runewizard.com/api/diablo-clone-progress/all")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", 0))
TOKEN_DC = os.environ.get("DISCORD_TOKEN")
TOKEN_D2RWZ = os.environ.get("D2RWZ_TOKEN")
FULL_DC_MSG_D2RIO = 1031507186179911691
MINIMUM_TB_LEVEL = 0



class Regions:
    AMERICAS = 1
    EUROPE = 2
    ASIA = 3
    FULLTEXT = {1: "Americas", 2: "Europe", 3: "Asia"}
    TEXT = {1: "AM", 2: "EU", 3: "AS"}


class Ladder:
    LADDER = 1
    NON_LADDER = 2
    FULLTEXT = {1: "Ladder", 2: "Non-ladder"}
    TEXT = {1: "Ladder", 2: "Non-ladder"}


class Hardcore:
    HARDCORE = 1
    SOFTCORE = 2
    FULLTEXT = {1: "Hardcore", 2: "Softcore"}
    TEXT = {1: "HC", 2: "SC"}


class SortDirection:
    ASCENDING = "a"
    DESCENDING = "d"


class SortKey:
    PROGRESS = "p"
    REGION = "r"
    LADDER = "l"
    HARDCORE = "h"
    TIMESTAMP = "t"


class msg_prefix:
    TEXT = {
        1: "Terror gazes upon Sanctuary",
        2: "Terror approaches Sanctuary",
        3: "Terror begins to form within Sanctuary",
        4: "Terror spreads across Sanctuary",
        5: "超级大菠萝即将降临", 
        #5:"Terror is about to be unleashed upon Sanctuary"
        6: "超级大菠萝已降临！"
    }

class CHANNEL_ID:
    SEL = {
        Ladder.LADDER: {
            Hardcore.HARDCORE: 1027889965327188038,
            Hardcore.SOFTCORE: 1027889844506075198
        },
        Ladder.NON_LADDER: {
            Hardcore.HARDCORE: 1027890122097696768,
            Hardcore.SOFTCORE: 1027890065801756732
        }
    }
    PERIOD = 1027894748675059762
    TEST = 894561623816155178


def get_runewizzard_tracker():

    token_params = {"token": TOKEN_D2RWZ}
    response = requests.get(API_D2RWZ_DC_PROCESS, params=token_params)
    if response.status_code != 200:
        print("[Error] error getting D2RWZ DC progress", response.status_code)
    return response.json() if response.status_code == 200 else None


d2rwz_checler = get_runewizzard_tracker()
