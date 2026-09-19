import discord

from discord import app_commands
from discord.ext import commands


class StopCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="stop",
        description="Stops the music and clears the queue"
    )
    async def stop(
        self,
        interaction: discord.Interaction
    ):
        voice_client = interaction.guild.voice_client

        if voice_client.is_playing():
            voice_client.stop()

            await interaction.response.send_message(
                "Music stopped."
            )
        else:
            await interaction.response.send_message(
                "No music is playing.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(StopCommand(bot))