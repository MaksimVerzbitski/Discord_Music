import discord

from discord import app_commands
from discord.ext import commands


class NextCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="next",
        description="Plays the next song in the queue"
    )
    async def next_song(
        self,
        interaction: discord.Interaction
    ):
        self.bot.current_song_index += 1

        if (
            self.bot.current_song_index
            < len(self.bot.song_queue)
        ):
            await self.bot.play_song(
                interaction,
                self.bot.song_queue[
                    self.bot.current_song_index
                ]
            )
        else:
            await interaction.response.send_message(
                "Reached the end of the queue."
            )


async def setup(bot):
    await bot.add_cog(
        NextCommand(bot)
    )