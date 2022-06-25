import discord
from discord.ext import commands
import youtube_dl


from youtube_search import YoutubeSearch


class music(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

    self.is_playing = False
    self.is_paused = False
    
    # [formatted_url, voice_channel, clear_url, given_text]
    self.music_queue = []
    self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    # Voice channel it is connected to
    self.vc = None


  def search_yt(self, text):
    # First we check if the given text is not a link
    if text.find("www.youtube.com") == -1:
      try:
        result = YoutubeSearch(text, max_results=1).to_dict()
        return("http://www.youtube.com" + result[0].get("url_suffix"))
      except:
        return "EMPTY"
    return text
  
  def play_next (self):
    if len(self.music_queue) > 0:
      self.is_playing = True

      url = self.music_queue[0][0]
      self.music_queue.pop(0)

      self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
      
    else:
      self.is_playing = False

  #not a discord command but infinite check
  async def play_music(self, ctx):
    if len(self.music_queue) > 0:
      self.is_playing = True

      url = self.music_queue[0][0]

      if self.vc == None or not self.vc.is_connected():
        self.vc = await self.music_queue[0][1].connect()
      else:
        # if the bot is connected to VC
        await self.vc.move_to(self.music_queue[0][1])

      await ctx.send("Now Playing: :musical_note: " + self.music_queue[0][2])
      self.music_queue.pop(0)
      
      self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())

    else:
      self.is_playing = False

  @commands.command(name = "play", aliases = ["p"])
  async def play (self, ctx, *args):
    text = " ".join(args)

    try:
      voice_channel = ctx.author.voice.channel

      if self.is_paused:
        self.vc.resume()
      else:
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
          url = self.search_yt(text)
          # We need to check if there was a match with the given text
          if url == "EMPTY":
            await ctx.send("I can't open this video, try again.")
          else:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            self.music_queue.append([url2, voice_channel, url, text])

            if not self.is_playing:
              await self.play_music(ctx)
            else:
              await ctx.send(url + " Added to the list :musical_note:")
    except:
      await ctx.send("You are not connected to a voice channel!")
      
    

          
  @commands.command(name="pause")
  async def pause(self, ctx, *args):
    if self.is_playing:
      self.is_playing = False
      self.is_paused = True
      self.vc.pause()
      await ctx.send("Paused.")
    elif self.is_paused:
      self.vc.resume()
      await ctx.send("Playing.")

  @commands.command(name = "resume", aliases=["r"])
  async def resume(self, ctx, *args):
    if self.is_paused:
      self.vc.resume()
      await ctx.send("Playing")

  @commands.command(name="skip", aliases=["s"])
  async def skip(self, ctx):
    if self.vc != None and self.vc:
      await ctx.send("Skipped :arrow_right:")
      self.vc.stop()
      await self.play_music(ctx)

  @commands.command(name="queue", aliases=["q"], help="Will display the current queue.")
  async def queue(self, ctx):
    retval = ""
    for i in range(0, len(self.music_queue)):
      retval += str(i+1) + " -->  " + self.music_queue[i][3] + "\n"

    if retval != "":
      await ctx.send("Music in the queue: \n" + retval)
    else:
     await ctx.send("Queue is empty. :pensive:")

  @commands.command(name="clear", aliases=["c", "bin"], help="Resets the entire queue")
  async def clear(self, ctx):
    if self.vc != None and self.is_playing:
       self.vc.stop()
    self.music_queue = []
    await ctx.send("Queue is cleared. :shower:")

  @commands.command(name="leave", aliases=["disconnect", "l", "d"])
  async def dc(self, ctx):
    await ctx.send("Adios :cowboy:")
    self.is_playing = False
    self.is_paused = False
    await self.vc.disconnect()