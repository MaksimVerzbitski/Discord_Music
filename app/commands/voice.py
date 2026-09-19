import logging

import discord
from discord import app_commands
from discord.ext import commands

from app.services.audio import play_entrance_sound


logger = logging.getLogger(__name__)


class VoiceCommands(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(
        name="join",
        description="Join your voice channel",
    )
    async def join(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        if interaction.user.voice is None:
            await interaction.response.send_message(
                "Join a voice channel first.",
                ephemeral=True,
            )
            return

        channel = interaction.user.voice.channel
        permissions = channel.permissions_for(interaction.guild.me)
        if not permissions.connect or not permissions.speak:
            await interaction.response.send_message(
                "I need Connect and Speak permissions in your voice channel.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)
        voice_client = interaction.guild.voice_client
        phase = "Voice connection"

        try:
            if voice_client is not None:
                logger.info(
                    "[VOICE] Existing voice client: connected=%s channel=%s",
                    voice_client.is_connected(),
                    voice_client.channel,
                )

                if voice_client.is_connected():
                    if voice_client.channel != channel:
                        logger.info(
                            "[VOICE] Moving to %s",
                            channel.name,
                        )

                        await voice_client.move_to(channel)

                else:
                    logger.warning(
                        "[VOICE] Found disconnected/stale voice client."
                    )

                    await voice_client.disconnect(
                        force=True
                    )

                    voice_client = None

            if voice_client is None:
                logger.info(
                    "[VOICE] Connecting to %s",
                    channel.name,
                )

                voice_client = await channel.connect()

            logger.info(
                "[VOICE] Connection ready: %s",
                voice_client.is_connected(),
            )

            # -------------------------------------------------
            # Discord voice-state diagnostics
            # -------------------------------------------------

            voice_state = interaction.guild.me.voice

            if voice_state is None:
                logger.warning(
                    "[VOICE STATE] guild.me.voice is None"
                )

            else:
                logger.info(
                    "[VOICE STATE] "
                    "channel=%s "
                    "mute=%s "
                    "deaf=%s "
                    "self_mute=%s "
                    "self_deaf=%s "
                    "suppress=%s",
                    voice_state.channel,
                    voice_state.mute,
                    voice_state.deaf,
                    voice_state.self_mute,
                    voice_state.self_deaf,
                    getattr(
                        voice_state,
                        "suppress",
                        None,
                    ),
                )

            phase = "Entrance sound"
            if voice_state and (voice_state.mute or voice_state.self_mute):
                raise RuntimeError("Unmute the bot to hear the entrance sound.")
            if voice_state and voice_state.suppress:
                raise RuntimeError("Invite the bot to speak on the Stage first.")

            await interaction.edit_original_response(
                content=f"Joined **{channel.name}**."
            )

            await play_entrance_sound(
                voice_client
            )

        except Exception as exc:
            logger.exception(
                "[VOICE] /join failed"
            )

            detail = str(exc) if isinstance(exc, RuntimeError) else "Check the bot console for details."
            await interaction.edit_original_response(
                content=f"{phase} failed. {detail}",
            )
            
    @app_commands.command(
        name="leave",
        description="Leave the voice channel",
    )
    async def leave(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            return

        voice_client = interaction.guild.voice_client

        if voice_client is None:
            await interaction.response.send_message(
                "Bot is not in a voice channel.",
                ephemeral=True,
            )
            return

        logger.info(
            "[VOICE] Force disconnecting from %s",
            voice_client.channel,
        )

        await interaction.response.defer(thinking=True)
        await voice_client.disconnect(
            force=True
        )

        await interaction.edit_original_response(
            content="Left the voice channel."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(
        VoiceCommands(bot)
    )
