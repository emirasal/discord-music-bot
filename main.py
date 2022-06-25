import discord
from discord.ext import commands

from music import music

  
bot = commands.Bot(command_prefix = '.')

bot.add_cog(music(bot))

@bot.event
async def on_ready():
  print("Music Bot is now ONLINE")
  await bot.change_presence(activity = discord.Game(name=".play | .help"))

bot.run("INSERT YOUR BOT'S TOKEN HERE")
