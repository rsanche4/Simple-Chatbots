
#this right here, this script when ran should problably linked and start every other script

import openai 
import discord
from discord.ext import commands,tasks
from icrawler.builtin import GoogleImageCrawler
import asyncio
import extractor
import os

original_dir = os.getcwd()
current_dir = os.getcwd()
TOKEN = open("C:\\Users\\rsanz\\OneDrive\\Documents\\discordtoken.txt").readlines()[0]
openaikey = open("C:\\Users\\rsanz\\OneDrive\\Documents\\openaikey.txt").readlines()[0]
lisa_personality = open("persona.txt").readlines()[0]
clientOpenAi = openai.OpenAI(
    api_key=openaikey
)
messages = [ {"role": "system", "content":  
              lisa_personality} ] 

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!',intents=intents)

ffmpeg_options = {
    'options': '-vn'
}

# Beware navigating through computer can crash audio since its relative
@bot.command(name="cd", help="Generate ai image")
async def on_message(ctx,changedir):
    global current_dir
    async with ctx.typing():
        parts = current_dir.split("\\")
        if changedir=='' or changedir=='~' or changedir=='/':
            current_dir = original_dir
        elif changedir=='..' and len(parts) > 0:
            current_dir = "\\".join(parts[:-1])
        elif changedir!='.' and changedir!='..' and len(parts) > 0:
            parts.append(changedir)
            print(parts)
            current_dir = "\\".join(parts)
        try:
            os.chdir(current_dir)
            await ctx.send(current_dir)
        except:
            current_dir = "\\".join(parts[:-1])
            await ctx.send("Not a valid directory!")
@bot.command(name="pwd", help="Generate ai image")
async def on_message(ctx):
    async with ctx.typing():
        await ctx.send(current_dir)
@bot.command(name="ls", help="Generate ai image")
async def on_message(ctx):
    async with ctx.typing():
        listofdirs = os.listdir(current_dir)
        for i in range(0, len(listofdirs)):
            listofdirs[i]= listofdirs[i]+'\n'
        listofdirs = "".join(listofdirs)
        await ctx.send(listofdirs)
@bot.command(name="cat", help="note to self")
async def on_message(ctx,file):
    async with ctx.typing():
        with open(file, "r") as file:
            contents = file.read()
            await ctx.send(contents)

@bot.command(name="imagine", help="Generate ai image")
async def on_message(ctx):
    async with ctx.typing():
        response = clientOpenAi.images.generate(
            model="dall-e-3",
            prompt=ctx.message.content[9:],
            size="1024x1024",
            quality="standard",
            n=1
        )
        await ctx.send(response.data[0].url)

@bot.command(name="toselfshow", help="note to self")
async def on_message(ctx):
    async with ctx.typing():
        with open("note.txt", "r") as file:
            contents = file.read()
            await ctx.send("Notes to self:\n"+contents)

@bot.command(name="toself", help="note to self")
async def on_message(ctx):
    async with ctx.typing():
        with open("note.txt", "a") as file:
            file.write(ctx.message.content[8:] + "\n")
        await ctx.send("Your note to self was added.")

@bot.command(name="deletetoself", help="note to self")
async def on_message(ctx):
    async with ctx.typing():
        with open("note.txt", "a") as file:
            file.truncate(0)
        await ctx.send("Your notes were deleted.")

@bot.command(name="todoadd", help="takes a todo list note")
async def on_message(ctx):
    async with ctx.typing():
        with open("todo.txt", "a") as file:
            file.write("+ "+ ctx.message.content[9:] + "\n")
        await ctx.send("Todo added.")

@bot.command(name="tododone", help="takes a todo list note")
async def on_message(ctx):
    async with ctx.typing():
        with open("todo.txt", "w") as file:
            file.truncate(0)
            await ctx.send("Your todo list was cleaned. No more todos!")

@bot.command(name="todo", help="takes a todo list note")
async def on_message(ctx):
    async with ctx.typing():
        with open("todo.txt", "r") as file:
            contents = file.read()
            await ctx.send("Here is your todo list:\n"+contents)

@bot.command(name='play', help='Tells the bot to join the voice channel')
async def join(ctx,url):
    async with ctx.typing():
        extractor.delete_files_in_folder("sound")
        extractor.youtube_audio_extractor(url, "C:\\Users\\rsanz\\OneDrive\\Documents\\GithubRepos\\AI-Projects\\Discordbot\\sound")
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
            try:
                await channel.connect()
                filename = "sound\\song.mp3"
                server = ctx.message.guild
                voice_channel = server.voice_client
                voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe", source=filename))
            except: #already connected
                filename = "sound\\song.mp3"
                server = ctx.message.guild
                voice_channel = server.voice_client
                voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe", source=filename))

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    async with ctx.typing():
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.stop()

@bot.command(name='t', help='Talking to the bot')
async def on_message(ctx):
    async with ctx.typing():
        messages.append( 
            {"role": "user", "content": ctx.message.content[6:]}, 
        ) 
        chat = clientOpenAi.chat.completions.create( 
            model="gpt-3.5-turbo", messages=messages, stream=False 
        ) 
        reply = chat.choices[0].message.content 
        messages.append({"role": "assistant", "content": reply})
        await ctx.send(reply)

@bot.command(name='shutdown', help='Talking to the bot')
async def on_message(ctx):
    async with ctx.typing():
        await ctx.send("Shutting down...")
        exit()

bot.run(TOKEN)
