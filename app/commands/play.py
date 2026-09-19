import logging

import discord

from discord import app_commands
from discord.ext import commands

from app.music_bot import YTDLSource


logger = logging.getLogger(__name__)


class PlayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="play",
        description="Plays a song from YouTube"
    )
    @app_commands.describe(
        search="The song to search or play from YouTube"
    )
    async def play(
        self,
        interaction: discord.Interaction,
        search: str
    ):
        await interaction.response.defer()

        voice_client = interaction.guild.voice_client

        if not voice_client:
            await interaction.followup.send(
                "❌ Bot is not in a voice channel. Use `/join` first."
            )
            return

        logger.info(f"🔍 Searching YouTube for: {search}")

        video_url = await YTDLSource.search(
            search,
            loop=self.bot.loop
        )

        if (
            isinstance(video_url, str)
            and video_url.startswith("An error occurred")
        ):
            await interaction.followup.send(video_url)
            return

        try:
            player = await YTDLSource.from_url(
                video_url,
                loop=self.bot.loop
            )

            if isinstance(player, str):
                await interaction.followup.send(player)
                return

            voice_client.play(
                player,
                after=lambda e: logger.info(
                    f"Playback finished. Error: {e}"
                ) if e else None
            )

            await interaction.followup.send(
                f"✅ **Now playing:** {player.data['title']}"
            )

        except Exception as e:
            logger.error(f"❌ Error playing song: {e}")

            await interaction.followup.send(
                f"❌ Failed to play song: {e}"
            )


async def setup(bot):
    await bot.add_cog(PlayCommand(bot))