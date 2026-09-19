import discord

from discord import app_commands
from discord.ext import commands


class ShuffleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="shuffle",
        description=(
            "Shuffles and plays the music queue "
            "randomly from local files"
        )
    )
    async def shuffle(
        self,
        interaction: discord.Interaction
    ):
        song_queue = self.bot.get_local_songs()

        self.bot.song_queue.clear()
        self.bot.song_queue.extend(song_queue)

        if not self.bot.song_queue:
            await interaction.response.send_message(
                "No songs found in the local directory."
            )
            return

        await self.bot.play_next_song(
            interaction
        )


async def setup(bot):
    await bot.add_cog(
        ShuffleCommand(bot)
    )