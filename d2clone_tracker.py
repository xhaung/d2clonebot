import os
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv
import requests

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://diablo2.io/dclone_api.php")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", 0))
TOKEN = os.environ.get("DISCORD_TOKEN")


class Regions:
    AMERICAS = 1
    EUROPE = 2
    ASIA = 3
    TEXT = {1: "Americas", 2: "Europe", 3: "Asia"}


class Ladder:
    LADDER = 1
    NON_LADDER = 2
    TEXT = {1: "Ladder", 2: "Non-ladder"}


class Hardcore:
    HARDCORE = 1
    SOFTCORE = 2
    TEXT = {1: "Hardcore", 2: "Softcore"}


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
        6: "超级大菠萝已降临"
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


bot = commands.Bot(command_prefix="!")


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
    return response.json() if response.status_code == 200 else None

def init_record_list():
    record_list = dict()
    checker = get_diablo_tracker()

    for entry in checker:
        key = (int(entry["region"]), int(entry["ladder"]), int(entry["hc"]))
        record_list[key] = 0

    return record_list


def check_new_entry(tracker, levels, record_list):
    new_entry = dict()
    
    for entry in tracker:
        key = (int(entry["region"]), int(entry["ladder"]), int(entry["hc"]))
        progress = int(entry["progress"])

        if progress in levels and progress > record_list[key]:
            new_entry[key] = progress

        record_list[key] = progress
                    
    return new_entry

def build_msg_str(key, progress):
    return f"**[{progress}/6]** {msg_prefix.TEXT[progress]} {'|'} {Regions.TEXT[key[0]]} {Ladder.TEXT[key[1]]} {Hardcore.TEXT[key[2]]}\n"


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

    await bot.process_commands(message)


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

    
record_list = init_record_list()
        
@tasks.loop(seconds=60.0)
async def notify_loop():
    #print("testing 1")
    checker = get_diablo_tracker()
    new_entry = check_new_entry(checker, [4, 5, 6], record_list)

    for key in new_entry:
        progress = new_entry[key]
        message = build_msg_str(key, progress)
        print(message)
        channel_id = CHANNEL_ID.SEL[key[1]][key[2]]
        channel = bot.get_channel(channel_id)
        await channel.send(message)
    

@notify_loop.before_loop
async def before_notify_loop():
    print('waiting...')
    await bot.wait_until_ready()


@tasks.loop(hours=4.0)
async def period_loop():
    #print("testing 1")
    checker = get_diablo_tracker()
    list_entry = check_new_entry(checker, [3, 4, 5, 6])
    
    message = "---- Current terror progress ----\n"
    for key in list_entry:
        progress = list_entry[key]
        message += build_msg_str(key, progress)
        
    if len(list_entry) == 0:
        message += "No region's terror progresses beyond 3 at the moment"
        
    channel_id = CHANNEL_ID.TEST
    # print(channel_id, message)
    await channel.send(message)
    

@period_loop.before_loop
async def before_period_loop():
    print('waiting...')
    await bot.wait_until_ready()
    

notify_loop.start()
period_loop.start()
bot.run(TOKEN)


