import os
import discord
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
import requests
import collections 
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
import pytz

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://diablo2.io/dclone_api.php")
API_D2RWZ_DC_PROCESS = os.environ.get("API_D2RWZ_DC_PROCESS", "https://d2runewizard.com/api/diablo-clone-progress/all")
API_D2RWZ_TZ = os.environ.get("API_D2RWZ_DC_PROCESS", "https://d2runewizard.com/api/terror-zone")
API_D2RWZ_WALK = os.environ.get("API_D2RWZ_WALK", "https://d2runewizard.com/api/diablo-clone-progress/planned-walks")
IS_WEB_WORKER = int(os.environ.get("IS_WEB_WORKER", 0))

TOKEN_DC = os.environ.get("DISCORD_TOKEN")
TOKEN_D2RWZ = os.environ.get("D2RWZ_TOKEN")

MINIMUM_TB_LEVEL = 0

MSG_ID_FULL_DC_D2RIO = 1031507186179911691
MSG_ID_TZ_D2RWZD = 1031617016366366800


LOOP_INTV_WALK = 60


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

class top_terror_zone:
    LIST = [
        "Moo Moo Farm",
        "Chaos Sanctuary",
        "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
        "Tal Rasha's Tombs and Tal Rasha's Chamber",
        "Travincal",
        "The Pit",
        "Arcane Sanctuary",
        "The Forgotten Tower",
        "Nihlathak's Temple, Halls of Anguish, Halls of Pain, and Halls of Vaught",
        "Tristram",
        "Cathedral and Catacombs"
    ]
    
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
    TZ_NOTIFY = 1031688784565248051

def tx_hc(hc):
    return 1 if hc else 2

def tx_l(l):
    return 1 if l else 2

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())


def get_diablo_tracker(
    region=None, ladder=None, hardcore=None, sort_key=None, sort_direction=None
):
    params = {
        "region": region,
        "ladder": ladder,
        "hc": hardcore,
        "sk": sort_key,
        "sd": sort_direction,
    }
    filtered_params = {k: v for k, v in params.items() if v is not None}
    headers = {"User-Agent": "d2clone-discord"}
    response = requests.get(API_BASE_URL, params=filtered_params, headers=headers)
    if response.status_code != 200:
        print("[Error] error getting progress", response.status_code)
    return response.json() if response.status_code == 200 else None

def get_runewizzard_tracker(api_addr):
    token_params = {"token": TOKEN_D2RWZ}
    response = requests.get(api_addr, params=token_params)
    if response.status_code != 200:
        print("[Error] error getting D2RWZ DC progress", response.status_code)
    return response.json() if response.status_code == 200 else None


def init_record_list(real_value = False, sort_list = False):
    record_list = OrderedDict()
    checker = get_diablo_tracker()

    for entry in checker:
        key = (int(entry["region"]), int(entry["ladder"]), int(entry["hc"]))
        record_list[key] = int(entry["progress"]) if real_value else 0

    if sort_list:
        record_list = collections.OrderedDict(sorted(record_list.items()))

    return record_list


def check_new_entry(tracker, levels, record_list=None):
    new_entry = OrderedDict()
    
    for entry in tracker:
        key = (int(entry["region"]), int(entry["ladder"]), int(entry["hc"]))
        progress = int(entry["progress"])

        if progress in levels and (record_list is None or progress > record_list[key]):
            new_entry[key] = progress

        if record_list is not None:
            record_list[key] = progress
    
    new_entry = collections.OrderedDict(sorted(new_entry.items()))
    return new_entry

## Message handling ###

def get_time_from_seconds(seconds):
    utc_now = pytz.utc.localize(datetime(1970,1,1) + timedelta(seconds=seconds))
    pst_now = utc_now.astimezone(pytz.timezone("CET"))

    return pst_now


def build_msg_str(key, progress, with_msg_prefix = False, with_credict = True, full_text=False):
    prefix = msg_prefix.TEXT[progress] if with_msg_prefix else ''
    if full_text:
        text = f"**[{progress}/6]** {prefix} {'|'} **{Regions.FULLTEXT[key[0]]} {Ladder.FULLTEXT[key[1]]} {Hardcore.FULLTEXT[key[2]]}**"
    else:
        text = f"**[{progress}/6]** {prefix} {'|'} **{Regions.TEXT[key[0]]} {Ladder.TEXT[key[1]]} {Hardcore.TEXT[key[2]]}**"
    if with_credict:
        text += "\n> Data courtesy of diablo2.io"
    return text

def create_tz_msg(tz_info):
    z = tz_info['terrorZone']
    
    pst_now = get_time_from_seconds(z['lastUpdate']['seconds'])
    
    string = f"--- ***Terror Zone (D2RuneWizzard)*** ---\n\n"
    string += f"Act: ***{z['act']}***\n"
    string += f"Zone: ***{z['zone']}***\n"
    string += f"Last Updated: {pst_now.time()} (CET)\n"
    string += f"Reports (Probability): {z['highestProbabilityZone']['amount']}" + f" ({z['highestProbabilityZone']['probability']*100}%)\n"
    string += f"> Provided by: <{tz_info['providedBy']}>\n"
    print(f"Time {pst_now.time()}, Act {z['act']}, Zone {z['zone']}")

    return string

def create_planned_walk_msg(walk, provided = None):
    print(datetime.fromtimestamp(walk['timestamp']/1000), "\n")

    text = "--- ***Planned DC Walk*** ---\n"
    text += f"***{Ladder.FULLTEXT[tx_l(walk['ladder'])]}, {Hardcore.FULLTEXT[tx_hc(walk['hardcore'])]}, {walk['region']}***\n"
    text += f"Time: {get_time_from_seconds(walk['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += f"Confimred: {walk['confirmed']}\n"
    text += f"By: {walk['displayName']}\n"
    text += f"Source: <{walk['source']}>\n"

    if provided != None:
        text += "> Provided by <" + provided + ">\n"

    return text



def status_text(list, region=None, ladder=None, hardcore=None, fulltext=False):
    text = ""
    for key, value in list.items():
        if filter_realm(key, region, ladder, hardcore):
            if fulltext:
                text += f"**[{value}/6]**   {Regions.FULLTEXT[key[0]]} {Ladder.FULLTEXT[key[1]]} {Hardcore.FULLTEXT[key[2]]}\n"
            else:
                text += f"**[{value}/6]**   {Regions.TEXT[key[0]]} {Ladder.TEXT[key[1]]} {Hardcore.TEXT[key[2]]}\n"
    text += "> Data courtesy of diablo2.io"
    return text



def filter_realm(key, region, ladder, hardcore):
    return (
        (not region or key[0] == region)
        and (not ladder or key[1] == ladder)
        and (not hardcore or key[2] == hardcore)
    )


def parse_args(args):
    if not args:
        return None, None, None

    region = None
    ladder = None
    hardcore = None

    if any("am" in arg for arg in args):
        region = Regions.AMERICAS
    if any("eu" in arg for arg in args):
        region = Regions.EUROPE
    if any("asi" in arg for arg in args):
        region = Regions.ASIA

    if any("non" in arg for arg in args):
        ladder = Ladder.NON_LADDER
    if any("ladder" in arg for arg in args) and not any("non" in arg for arg in args):
        ladder = Ladder.LADDER

    if any("hard" in arg for arg in args):
        hardcore = Hardcore.HARDCORE
    if any("soft" in arg for arg in args):
        hardcore = Hardcore.SOFTCORE

    return region, ladder, hardcore



print(type(IS_WEB_WORKER), IS_WEB_WORKER, "\n")

if IS_WEB_WORKER:

    """
    def channel_send_msg(channel_id, msg):
        try:
            print(channel_id, msg)
            channel = bot.get_channel(channel_id)
            await channel.send(msg)
        except Exception as e:
            print("[Error]:", e)
    """

    @bot.event
    async def on_ready():
        print(f'{bot.user} succesfully logged in!')

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        
        if message.content == 'hello':
            await message.channel.send(f'Hi {message.author}')
        if message.content == 'bye':
            await message.channel.send(f'Goodbye {message.author}')
            
        if message.content.startswith("!uberdiablo") and "help" in message.content:
            await message.channel.send("Usage: !uberdiablo [eu|am|asi] [non|ladder] [soft|hard]")
        elif message.content.startswith("!uberdiablo"):
            current_list = init_record_list(True, True)

            args = message.content.split(" ")[1:]
            region, ladder, hardcore = parse_args(args)
            text_message = status_text(
                list = current_list, 
                region=region, ladder=ladder, hardcore=hardcore
            )
            await message.channel.send(text_message)

        await bot.process_commands(message)

    """
    # Start each command with the @bot.command decorater
    @bot.command()
    async def square(ctx, arg): # The name of the function is the name of the command
        print(arg) # this is the text that follows the command
        await ctx.send(int(arg) ** 2) # ctx.send sends text in chat

    @bot.command()
    async def scrabblepoints(ctx, arg):
        # Key for point values of each letter
        score = {"a": 1, "c": 3, "b": 3, "e": 1, "d": 2, "g": 2,
            "f": 4, "i": 1, "h": 4, "k": 5, "j": 8, "m": 3,
            "l": 1, "o": 1, "n": 1, "q": 10, "p": 3, "s": 1,
            "r": 1, "u": 1, "t": 1, "w": 4, "v": 4, "y": 4,
            "x": 8, "z": 10}
        points = 0
        # Sum the points for each letter
        for c in arg:
            points += score[c]
        await ctx.send(points)
    """

    record_list = init_record_list(True)
    first_loop = False
            
    @tasks.loop(seconds=62.0)
    async def notify_loop():
        #print("testing 1")
        checker = get_diablo_tracker()
        if checker is not None:
            ## Print per channel update
            new_entry = check_new_entry(checker, [3, 4, 5, 6], record_list)

            for key in new_entry:
                progress = new_entry[key]
                message = build_msg_str(key, progress)
                channel_id = CHANNEL_ID.SEL[key[1]][key[2]]
                # channel_send_msg(channel_id, message)

                try:
                    print(channel_id, message)
                    channel = bot.get_channel(channel_id)
                    await channel.send(message)
                except Exception as e:
                    print("[Error]:", e)
            
            ## Print full table update

            list_entry = check_new_entry(checker, range(MINIMUM_TB_LEVEL, 6, 1))

            text = "\n--- ***Terror progress (Diablo2.io)*** ---\n"
            # datetime object containing current date and time
            utc_now = pytz.utc.localize(datetime.utcnow())
            pst_now = utc_now.astimezone(pytz.timezone("CET"))
            pst_str = pst_now.strftime("%H:%M:%S")
            text += "| Last updated: " +  pst_str + " (CET)\n\n"
            
            for key in list_entry:
                progress = list_entry[key]
                text += build_msg_str(key, progress, with_credict=False, full_text=True) + "\n"

            if len(list_entry) == 0:
                text += "No region's terror progresses beyond {MINIMUM_TB_LEVEL+1} at the moment\n"

            text += "> Data courtesy of diablo2.io"

            #print(message)
            channel_id = CHANNEL_ID.PERIOD
            #channel_send_msg(channel_id, message)
            try:
                print(channel_id, "last full update: " + pst_str)
                channel = bot.get_channel(channel_id)
                message = await channel.fetch_message(MSG_ID_FULL_DC_D2RIO)
                await message.edit(content=text)
                # await channel.send(message)
            except Exception as e:
                print("[Error]:", e)

        

    @notify_loop.before_loop
    async def before_notify_loop():
        print('waiting...')
        await bot.wait_until_ready()

    """
    @tasks.loop(hours=6.0)
    async def period_loop():
        global first_loop
        if not first_loop:
            checker = get_diablo_tracker()
            if checker is not None:
                list_entry = check_new_entry(checker, range(MINIMUM_TB_LEVEL, 6, 1))

                text = "--- ***Terror progress (Diablo2.io)*** ---\n"
                for key in list_entry:
                    progress = list_entry[key]
                    text += build_msg_str(key, progress, with_credict=False, full_text=True) + "\n"

                if len(list_entry) == 0:
                    text += "No region's terror progresses beyond {MINIMUM_TB_LEVEL+1} at the moment\n"

                text += "> Data courtesy of diablo2.io"

                #print(message)
                channel_id = CHANNEL_ID.PERIOD
                #channel_send_msg(channel_id, message)
                try:
                    print(channel_id, text)
                    channel = bot.get_channel(channel_id)
                    message = await channel.fetch_message(FULL_DC_MSG_D2RIO)
                    await message.edit(content=text)
                    # await channel.send(message)
                except Exception as e:
                    print("[Error]:", e)
        else:
            print("skipped the first hourly loop")
        
        first_loop = False
        

    @period_loop.before_loop
    async def before_period_loop():
        print('waiting...')
        await bot.wait_until_ready()
        
        
    period_loop.start()

    """

    TZ_TIME = 180
    previous_zone = ""
    skip_first_notify = True

    @tasks.loop(seconds=TZ_TIME)
    async def tz_loop():
        global TZ_TIME
        global previous_zone
        global skip_first_notify
        checker = get_runewizzard_tracker(API_D2RWZ_TZ)
        if checker is not None:
            ## Update waiting time
            current_minutes = datetime.utcnow().strftime("%M")
            TZ_TIME = max(30, min((60 - int(current_minutes)), checker['terrorZone']['highestProbabilityZone']['amount'])*60)
            print(f"Time:{current_minutes}, Amount:{checker['terrorZone']['highestProbabilityZone']['amount']} ,TZ_TIME:{TZ_TIME}\n")
            tz_loop.change_interval(seconds=TZ_TIME)
            
            text = create_tz_msg(checker)
            
            #print(message)
            channel_id = CHANNEL_ID.PERIOD
            try:
                # print(channel_id, "last tz: " + text)
                channel = bot.get_channel(channel_id)
                message = await channel.fetch_message(MSG_ID_TZ_D2RWZD)
                await message.edit(content=text)
                
                # channel_id = CHANNEL_ID.PERIOD
                # channel = bot.get_channel(channel_id)
                # await channel.send(text)
            except Exception as e:
                print("[Error]:", e)
                
            ## notification
            try:
                current_zone = checker['terrorZone']['zone']
                if current_zone in top_terror_zone.LIST and current_zone != previous_zone and not skip_first_notify:
                    notify_text = f"***TOP {top_terror_zone.LIST.index(current_zone) + 1}*** out of {len(top_terror_zone.LIST)} most popular terror zones\n"
                    notify_text += text
                    channel_id = CHANNEL_ID.TZ_NOTIFY
                    channel = bot.get_channel(channel_id)
                    await channel.send(notify_text)
                previous_zone = current_zone
                skip_first_notify = False
            except Exception as e:
                print("[Error]:", e)
        

    @tz_loop.before_loop
    async def before_tz_loop():
        print('tz loop waiting...')
        await bot.wait_until_ready()
    """
    @tz_loop.after_loop
    async def after_tz_loop():
        print("TZ loop time changed to ", TZ_TIME)
        tz_loop.change_interval(TZ_TIME)
    """

    planned_walk_history = OrderedDict()
    skip_initial_walks = False

    @tasks.loop(seconds=LOOP_INTV_WALK)
    async def walk_loop():
        global skip_initial_walks
        global planned_walk_history
        checker = get_runewizzard_tracker(API_D2RWZ_WALK)

        if checker is not None:
            
            channel_id = CHANNEL_ID.TEST
            channel = bot.get_channel(channel_id)
            
            for walk in checker['walks']:
                text = create_planned_walk_msg(walk, checker['providedBy'])

                if walk['id'] not in planned_walk_history:
                    planned_walk_history['id'] = walk['displayName']
                    print("walk", walk['id'], "\n", text)

                    if not skip_initial_walks:
                        try:
                            message = await channel.send(text)
                            planned_walk_history[walk['id']] = message.id
                        except Exception as e:
                            print("[Error]:", e)
                else:
                    try:
                        message = await channel.fetch_message(planned_walk_history[walk['id']])
                        await message.edit(content=text)
                    except Exception as e:
                        print("[Error]:", e)
            
        if len(planned_walk_history) > 128:
            for i in range(0, len(planned_walk_history) - 129):
                print("deleting item (->:", len(planned_walk_history), "), ", next(iter(planned_walk_history.items())), "\n")
                planned_walk_history.popitem()


    @walk_loop.before_loop
    async def before_walk_loop():
        print('walk loop waiting...')
        await bot.wait_until_ready()


    notify_loop.start()
    tz_loop.start()
    walk_loop.start()
    bot.run(TOKEN_DC)

else:
    print("this is the testing flow\n")
    
    """

    #checker = get_runewizzard_tracker(API_D2RWZ_WALK)
    planned_walk_history = OrderedDict()
    planned_walk_history['BsFOBOodpvTkncc3LRb8'] = 23131241545346234

    checker = {'walks': [{'id': 'aMZcS4bSZD2BgDe6mlY6', 'displayName': 'Przemysław “Sky” Zawada', 'ladder': False, 'region': 'TBD', 'hardcore': False, 'uid': 'hX1xfQ3AtzgtiQaprJIryDaozAm2', 'confirmed': False, 'timestamp': 1666353600000, 'source': 'https://discord.com/channels/892856193536622602/895727392092459049/1032670723031969813'}, {'id': 'BsFOBOodpvTkncc3LRb8', 'timestamp': 1666357200000, 'confirmed': False, 'hardcore': False, 'uid': '2SQSuQFxokPMduAMx4o4cF11yrE3', 'displayName': 'synse', 'source': 'https://discord.com/channels/892856193536622602/1020301862886449174/1032290349009350687', 'region': 'TBD', 'ladder': True}, {'id': 'FbiweNhh2B0bgivQiWiC', 'hardcore': False, 'confirmed': True, 'source': 'https://www.youtube.com/c/FBI%EB%A9%80%EB%8D%942', 'timestamp': 1666429200000, 'displayName': 'spyder', 'ladder': True, 'uid': '0BInXYohKweLOBBjWWSzm40N3zu2', 'region': 'Asia'}], 'providedBy': 'https://d2runewizard.com/diablo-clone-tracker'}
    # print(checker)

    channel_id = CHANNEL_ID.TEST
    channel = bot.get_channel(channel_id)
    skip_initial_walks = False

    skip_initial_walks
    for walk in checker['walks']:
        text = create_planned_walk_msg(walk, checker['providedBy'])

        if walk['id'] not in planned_walk_history:
            planned_walk_history['id'] = walk['displayName']
            print("walk", walk['id'], "\n", text)

            if not skip_initial_walks:
                message = await channel.send(text)
                planned_walk_history[walk['id']] = message.id
        else:
            
            message = await channel.fetch_message(planned_walk_history[walk['id']])
            await message.edit(content=text)

    if len(planned_walk_history) > 0:
        for i in range(0, len(planned_walk_history) - 1):
            print("deleting item:", next(iter(planned_walk_history.items())))
            planned_walk_history.popitem()
            print(len(planned_walk_history))

    """
