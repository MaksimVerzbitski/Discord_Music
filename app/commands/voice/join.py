import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENTRANCE_SOUND = (
    PROJECT_ROOT
    / "sounds"
    / "nokia-tune-1600-36527.mp3"
)


class JoinCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="join",
        description="Tells the bot to join the voice channel",
    )
    async def join(self, interaction: discord.Interaction):
        logger.info("Attempting to join a voice channel...")

        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not interaction.user.voice:
            await interaction.response.send_message(
                "You are not connected to a voice channel.",
                ephemeral=True,
            )
            return

        channel = interaction.user.voice.channel

        await interaction.response.defer(thinking=True)

        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_connected():
            if voice_client.channel != channel:
                logger.info(
                    "Moving from %s to %s.",
                    voice_client.channel.name,
                    channel.name,
                )
                await voice_client.move_to(channel)
            else:
                logger.info(
                    "Bot is already connected to %s.",
                    channel.name,
                )
        else:
            voice_client = await channel.connect()
            logger.info("Joined %s successfully.", channel.name)

        await interaction.edit_original_response(
            content=f"Joined **{channel.name}**."
        )

        if not ENTRANCE_SOUND.is_file():
            logger.error(
                "Entrance sound does not exist: %s",
                ENTRANCE_SOUND,
            )
            return

        if voice_client.is_playing():
            logger.info(
                "Audio is already playing; entrance sound skipped."
            )
            return

        try:
            source = discord.FFmpegPCMAudio(str(ENTRANCE_SOUND))

            voice_client.play(
                source,
                after=lambda error: logger.error(
                    "Entrance sound playback error: %s",
                    error,
                )
                if error
                else logger.info(
                    "Entrance sound finished playing."
                ),
            )

            logger.info(
                "Playing entrance sound: %s",
                ENTRANCE_SOUND,
            )

        except Exception:
            logger.exception("Failed to start entrance sound.")


async def setup(bot: commands.Bot):
    await bot.add_cog(JoinCommand(bot))