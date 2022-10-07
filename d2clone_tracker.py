import os
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

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

record_list_5 = dict()
record_list_6 = dict()


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

def check_new_entry(tracker, lv, record_list):
    updated_tracker = dict()
    for entry in tracker:
        key = (int(entry["region"]), int(entry["ladder"]), int(entry["hc"]))
        if int(entry["progress"]) == lv:
            if key not in record_list:
                updated_tracker[key] = entry
                record_list[key] = entry
        else:
            if key in record_list:
                record_list.pop(key)
    return updated_tracker

def build_msg_str(key, progress):
    return f"**[{progress}/6]** {Regions.TEXT[key[0]]} {Ladder.TEXT[key[1]]} {Hardcore.TEXT[key[2]]}\n"


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

        
@tasks.loop(minutes=1.0)
async def myloop():
    print("testing 1")
    channel = bot.get_channel(894561623816155178)
    # await channel.send('Example message')
    
    checker = get_diablo_tracker()
    new_entry_5 = check_new_entry(checker, 2, record_list_5)
    new_entry_6 = check_new_entry(checker, 3, record_list_6)

    for key in new_entry_5:
        progress = int(new_entry_5[key]["progress"])
        message = build_msg_str(key, progress)
        await channel.send(message)

    for key in new_entry_6:
        progress = int(new_entry_6[key]["progress"])
        message = build_msg_str(key, progress)
        await channel.send(message)

@myloop.before_loop
async def before_myloop():
    print('waiting...')
    await bot.wait_until_ready()
        
# myloop.start()
bot.run(TOKEN)

