import logging

import discord
from discord import app_commands
from discord.ext import commands


logger = logging.getLogger(__name__)


class LeaveCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="leave",
        description="Leaves the voice channel",
    )
    async def leave(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            channel_name = voice_client.channel.name

            if voice_client.is_playing():
                voice_client.stop()

            await voice_client.disconnect()

            logger.info(
                "Disconnected from voice channel %s.",
                channel_name,
            )

            await interaction.response.send_message(
                "The bot has left the voice channel."
            )

            return

        await interaction.response.send_message(
            "The bot is not connected to a voice channel.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveCommand(bot))