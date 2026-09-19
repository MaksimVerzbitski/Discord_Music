import asyncio

import discord

from discord import app_commands
from discord.ext import commands


class SearchCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="search",
        description=(
            "Searches for songs on YouTube "
            "and allows selection"
        )
    )
    @app_commands.describe(
        query="The search query to find songs on YouTube"
    )
    async def search(
        self,
        interaction: discord.Interaction,
        query: str
    ):
        voice_channel = interaction.guild.voice_client

        if not voice_channel:
            await interaction.response.send_message(
                "Bot is not connected to a voice channel. "
                "Use `/join` first.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        search_results = await self.bot.YTDLSource.search(
            query,
            loop=self.bot.loop
        )

        if not search_results:
            await interaction.followup.send(
                "No results found."
            )
            return

        if isinstance(search_results, str):
            await interaction.followup.send(
                search_results
            )
            return

        results_message = "\n".join(
            [
                f"{index + 1}. {title}"
                for index, (title, _) in enumerate(
                    search_results[:10]
                )
            ]
        )

        message = await interaction.followup.send(
            f"Search results:\n"
            f"{results_message}\n\n"
            "React to choose a song or ❌ to cancel.",
            wait=True
        )

        selection_emojis = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
            "❌",
        ]

        for emoji in selection_emojis:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return (
                user == interaction.user
                and str(reaction.emoji) in selection_emojis
                and reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=60.0,
                check=check
            )

            await message.clear_reactions()

            if str(reaction.emoji) == "❌":
                await interaction.followup.send(
                    "Search cancelled."
                )
            else:
                song_index = selection_emojis.index(
                    str(reaction.emoji)
                )

                if 0 <= song_index < len(search_results):
                    title, url = search_results[song_index]

                    player = await self.bot.YTDLSource.from_url(
                        url,
                        loop=self.bot.loop
                    )

                    if not player:
                        await interaction.followup.send(
                            "Failed to load the selected song."
                        )
                        return

                    if not voice_channel.is_playing():
                        voice_channel.play(
                            player,
                            after=lambda e: print(
                                f"Player error: {e}"
                            ) if e else None
                        )

                        await interaction.followup.send(
                            f"✅ **Now playing:** {title}\n"
                            "🎵 Enjoy your music!"
                        )
                    else:
                        await interaction.followup.send(
                            "Audio is already playing. "
                            "Please stop the current track first."
                        )

        except asyncio.TimeoutError:
            await message.clear_reactions()

            await interaction.followup.send(
                "No response in time."
            )


async def setup(bot):
    await bot.add_cog(
        SearchCommand(bot)
    )