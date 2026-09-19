import discord

from discord import app_commands
from discord.ext import commands


class ResumeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="resume",
        description="Resumes the music"
    )
    async def resume(
        self,
        interaction: discord.Interaction
    ):
        voice_client = interaction.guild.voice_client

        if voice_client and not voice_client.is_playing():
            voice_client.resume()

            await interaction.response.send_message(
                "Music resumed."
            )
        else:
            await interaction.response.send_message(
                "No music to resume.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(ResumeCommand(bot))