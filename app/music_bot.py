import sys
import os
import logging

from app.utils.console_style import setup_logging
from app.utils.dependency_check import check_dependencies

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    setup_logging()
    if not check_dependencies():
        raise SystemExit(1)

import ssl
import certifi
import asyncio
import discord
import random
import time

from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
import yt_dlp as youtube_dl
from dotenv import load_dotenv
from discord import app_commands

# Configure SSL context
ssl._create_default_https_context = ssl._create_unverified_context
ssl.create_default_context(cafile=certifi.where())

# Configure logging
logger = logging.getLogger(__name__)

# Global variables
song_queue = []
current_song_index = 0
music_dir = 'download/'

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

CHANNEL_ID2 = os.getenv('CHANNEL_ID')

USER_ID = os.getenv('USER_ID')
USER_MAX_ID = os.getenv('USER_MAX_ID')

class MusicBot(commands.Bot):
    async def login(self, token):
        self._login_started = time.perf_counter()
        await super().login(token)
        logger.info(
            "Login and startup setup finished in %.2fs; connecting to Gateway...",
            time.perf_counter() - self._login_started
        )

    async def setup_hook(self):
        logger.info(
            "Discord authentication/setup requests finished in %.2fs.",
            time.perf_counter() - self._login_started
        )

        await self.load_extension("app.commands.voice.join")
        await self.load_extension("app.commands.voice.leave")

        await self.load_extension("app.commands.music.play")
        await self.load_extension("app.commands.music.stop")
        await self.load_extension("app.commands.music.resume")
        await self.load_extension("app.commands.music.shuffle")
        await self.load_extension("app.commands.music.search")
        await self.load_extension("app.commands.music.next")
        await self.load_extension("app.commands.music.previous")

        await self.load_extension("app.commands.utility.reload")

        await self.load_extension("app.commands.love")

        started = time.perf_counter()
        logger.info("Syncing application commands...")
        synced = await self.tree.sync()

        logger.info(
            "Synced %d application commands in %.2fs.",
            len(synced),
            time.perf_counter() - started
        )

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

# Instantiate the bot
bot = MusicBot(command_prefix='!', intents=intents)

# Define the scheduler
scheduler = AsyncIOScheduler(timezone="Europe/Tallinn")


def log_download_progress(d):
    """Logs download progress for debugging."""
    if d['status'] == 'downloading':
        print(f"Downloading: {d['_percent_str']} - Speed: {d['_speed_str']} - ETA: {d['eta']}s")
    elif d['status'] == 'finished':
        print(f"Download complete: {d['filename']}")
        
        
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')

    default_recipient_id = USER_MAX_ID
    tatjana_recipient_id = USER_ID

    scheduler.add_job(send_love_message, CronTrigger(hour=9, minute=30), args=[default_recipient_id])
    scheduler.add_job(send_love_message, CronTrigger(hour=9, minute=45), args=[tatjana_recipient_id])

    scheduler.start()
    
def get_local_songs():
    return [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith(('.mp3', '.ogg', '.wav', '.webm'))]

async def play_local(interaction, song_path):
    voice_client = interaction.guild.voice_client
    if not voice_client:
        await interaction.response.send_message("The bot is not in a voice channel.")
        return

    # Wait for the file to finish downloading
    timeout = 10  # Max wait time
    while song_path.endswith(".part") and timeout > 0:
        print(f"Waiting for {song_path} to finish downloading...")
        time.sleep(1)
        timeout -= 1

    # Ensure the final file exists before playing
    if not os.path.exists(song_path):
        await interaction.response.send_message("Download failed or incomplete.")
        return

    if not voice_client.is_playing():
        voice_client.play(discord.FFmpegPCMAudio(song_path), after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(interaction), bot.loop))
        await interaction.response.send_message(f"✅ Now playing: {os.path.basename(song_path)}")
    else:
        await interaction.response.send_message("Audio is already playing. Please stop the current track first.")


class YTDLSource(discord.PCMVolumeTransformer):
    YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'outtmpl': 'download/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [log_download_progress],
        'extractor_retries': 10,
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {'options': '-vn'}

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume=volume)
        self.data = data
        self.title = data.get('title')
        print(f"Initialized YTDLSource with title: {self.title}")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        logger.info(f"🔄 Downloading from URL: {url}")
        ydl = youtube_dl.YoutubeDL(cls.YDL_OPTIONS)

        try:
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]  

            filename = ydl.prepare_filename(data).replace('.webm', '.mp3').replace('.m4a', '.mp3')

            # Wait if file is still being processed
            timeout = 30
            while filename.endswith(".part") and timeout > 0:
                logger.warning(f"⏳ Waiting for {filename} to finish downloading...")
                await asyncio.sleep(1)
                timeout -= 1

            if filename.endswith(".part") or not os.path.exists(filename):
                logger.error(f"❌ Download failed, file not found: {filename}")
                return "❌ Download failed or incomplete."

            return cls(discord.FFmpegPCMAudio(filename, **cls.FFMPEG_OPTIONS), data=data)
        except Exception as e:
            logger.error(f"❌ yt-dlp error: {e}")
            return f"❌ Failed to download song: {e}"
                
    @classmethod
    async def search(cls, search_query, *, loop=None, max_results=10):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,  # Allow errors instead of crashing
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'force_generic_extractor': True,  # Force fallback mode
            'extractor_retries': 10,
            'source_address': '0.0.0.0',
            'default_search': f'ytsearch{max_results}',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False))
                if 'entries' not in info or not info['entries']:
                    print(f"No entries found for search query: {search_query}")
                    return "No results found."
                results = [(entry['title'], entry['webpage_url']) for entry in info['entries'] if 'title' in entry and 'webpage_url' in entry]
                return results if results else "No results found."
            except Exception as e:
                print(f"An error occurred during search: {e}")
                return f"An error occurred: {e}"
    
        
def format_duration(duration):
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes}:{seconds:02}"

async def play_next_song(ctx):
    global current_song_index

    if song_queue:
        current_song_index = random.randint(0, len(song_queue) - 1)
        song_path = song_queue[current_song_index]
        await play_local(ctx, song_path)
    else:
        await ctx.send("The song queue is empty.")

async def play_song(interaction, song_path):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client.is_playing():
        await interaction.response.send_message("Already playing audio.")
        return

    voice_client.play(discord.FFmpegPCMAudio(song_path), after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(interaction), bot.loop))
    await interaction.response.send_message(f"Now playing: {os.path.basename(song_path)}")



async def send_love_message(recipient_id=None):
    try:
        channel = bot.get_channel(int(CHANNEL_ID))
        if channel:
            if recipient_id:
                await channel.send(f"<@{recipient_id}> :point_right:, I love you :open_hands: this much :pinching_hand: ❤️")
            else:
                await channel.send("Sending love to everyone! :heart:")
    except Exception as e:
        print(f"Error in send_love_message: {e}")



@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Command invoke error: {error.original}")
        logger.error(f"Command invoke error: {error.original}")
    else:
        await ctx.send("An error occurred while processing your command.")
        logger.error(f"Unexpected error: {error}")
        raise error

@bot.event
async def on_message(message):
    await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(TOKEN, reconnect=True, log_handler=None)
