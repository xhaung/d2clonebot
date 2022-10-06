import os
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "https://diablo2.io/dclone_api.php")
DISCORD_CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL_ID", 0))
TOKEN = os.environ.get("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!")

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

    
    
class MyCog(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=20.0)
    async def printer(self):
        print(self.index)
        self.index += 1
        channel = bot.get_channel(894561623816155178)
        await channel.send('Example message')

    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()
        
cog = MyCog
cog.start()
bot.run(TOKEN)

