import discord

from discord import app_commands
from discord.ext import commands


class ReloadCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="reload",
        description="Reloads a module."
    )
    @commands.is_owner()
    @app_commands.describe(
        extension="The extension to reload"
    )
    async def reload(
        self,
        interaction: discord.Interaction,
        extension: str
    ):
        if extension:
            try:
                await self.bot.reload_extension(
                    f"cogs.{extension}"
                )

                await interaction.response.send_message(
                    f"Reloaded `{extension}` cog."
                )

            except Exception as e:
                await interaction.response.send_message(
                    f"Error reloading `{extension}`: {e}"
                )
        else:
            await interaction.response.send_message(
                "No extension specified."
            )


async def setup(bot):
    await bot.add_cog(ReloadCommand(bot))