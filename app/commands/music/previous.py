import discord

from discord import app_commands
from discord.ext import commands


class PreviousCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="previous",
        description="Plays the previous song in the queue"
    )
    async def previous_song(
        self,
        interaction: discord.Interaction
    ):
        if self.bot.current_song_index > 0:
            self.bot.current_song_index -= 1

            await self.bot.play_song(
                interaction,
                self.bot.song_queue[
                    self.bot.current_song_index
                ]
            )
        else:
            await interaction.response.send_message(
                "This is the first song in the queue."
            )


async def setup(bot):
    await bot.add_cog(
        PreviousCommand(bot)
    )