import os
import asyncio
import discord

from datetime import datetime, timedelta
from apscheduler.triggers.date import DateTrigger
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pytz import timezone


load_dotenv(override=True)

CHANNEL_ID = os.getenv("CHANNEL_ID")
USER_ID = os.getenv("USER_ID")
USER_MAX_ID = os.getenv("USER_MAX_ID")

if not all((CHANNEL_ID, USER_ID, USER_MAX_ID)):
    raise RuntimeError(
        "CHANNEL_ID, USER_ID and USER_MAX_ID must be defined in .env"
    )

CHANNEL_ID = int(CHANNEL_ID)
USER_ID = int(USER_ID)
USER_MAX_ID = int(USER_MAX_ID)

TALLINN_TZ = timezone("Europe/Tallinn")

print(f"[LOVE CONFIG] CHANNEL_ID={CHANNEL_ID}")


class LoveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_love_message(self, recipient_id=None):
        try:
            print(f"[LOVE] Sending scheduled message to {recipient_id}")

            channel = self.bot.get_channel(CHANNEL_ID)

            if channel is None:
                print(f"[LOVE] Text channel {CHANNEL_ID} is not in bot cache.")
                return

            if not isinstance(channel, (discord.TextChannel, discord.Thread)):
                print(f"[LOVE] Channel {CHANNEL_ID} is not a text channel.")
                return

            if recipient_id:
                embed = discord.Embed(
                    title="💖 A little message for you",
                    description=(
                        f"<@{recipient_id}>\n\n"
                        "👉 **I love you 🫶 this much 🤏 ❤️**"
                    )
                )
                embed.set_footer(text="Sent with ❤️")

                await channel.send(
                    content=f"<@{recipient_id}>",
                    embed=embed
                )

            else:
                embed = discord.Embed(
                    title="💖 Love for everyone",
                    description="Sending love to everyone! ❤️"
                )
                await channel.send(embed=embed)

            print(f"[LOVE] Message sent to #{channel.name} ({channel.id}).")

        except discord.Forbidden:
            print(f"[LOVE] No permission to send to channel {CHANNEL_ID}.")

        except discord.HTTPException as e:
            print(f"[LOVE] Discord HTTP error: {e}")

        except Exception as e:
            print(f"[LOVE] Error sending message: {e}")

    @app_commands.command(
        name="love",
        description="Schedule a love message ❤️"
    )
    async def love(self, interaction: discord.Interaction):
        hour_embed = discord.Embed(
            title="💌 Love Message",
            description=(
                "⏰ **What hour should I send it?**\n\n"
                "Enter a value from `0` to `23`."
            )
        )

        await interaction.response.send_message(embed=hour_embed)

        def check_hour(msg):
            return (
                msg.author == interaction.user
                and msg.channel == interaction.channel
                and msg.content.isdigit()
                and 0 <= int(msg.content) <= 23
            )

        def check_minutes(msg):
            return (
                msg.author == interaction.user
                and msg.channel == interaction.channel
                and msg.content.isdigit()
                and 0 <= int(msg.content) <= 59
            )

        try:
            hour_msg = await self.bot.wait_for(
                "message",
                check=check_hour,
                timeout=30.0
            )
            hour = int(hour_msg.content)

            minute_embed = discord.Embed(
                title="💌 Love Message",
                description=(
                    f"⏰ Hour: **{hour:02}**\n\n"
                    "⏱️ **What minute should I send it?**\n\n"
                    "Enter a value from `0` to `59`."
                )
            )

            await interaction.followup.send(embed=minute_embed)

            minutes_msg = await self.bot.wait_for(
                "message",
                check=check_minutes,
                timeout=30.0
            )
            minutes = int(minutes_msg.content)

            sender_id = interaction.user.id
            recipient_id = (
                USER_ID if sender_id == USER_MAX_ID else USER_MAX_ID
            )

            now = datetime.now(TALLINN_TZ)
            run_time = now.replace(
                hour=hour,
                minute=minutes,
                second=0,
                microsecond=0
            )

            if run_time <= now:
                run_time += timedelta(days=1)

            self.bot.scheduler.add_job(
                self.send_love_message,
                DateTrigger(run_date=run_time),
                args=[recipient_id],
                id=(
                    f"love_message_"
                    f"{sender_id}_"
                    f"{recipient_id}_"
                    f"{run_time.timestamp()}"
                )
            )

            day_text = (
                "Today"
                if run_time.date() == now.date()
                else "Tomorrow"
            )

            confirmation = discord.Embed(
                title="💌 Love Scheduled",
                description=(
                    f"❤️ **Recipient:** <@{recipient_id}>\n"
                    f"🕒 **Time:** {run_time:%H:%M}\n"
                    f"📅 **Day:** {day_text}\n\n"
                    "✨ Your message is ready to go."
                )
            )

            await interaction.followup.send(embed=confirmation)

            print(f"[LOVE] Job scheduled: {run_time.isoformat()}")

        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⌛ Love scheduling expired",
                description=(
                    "No answer was received within 30 seconds.\n"
                    "Run `/love` to try again."
                )
            )

            await interaction.followup.send(embed=timeout_embed)

        except Exception as e:
            print(f"[LOVE] Error while scheduling: {e}")

            error_embed = discord.Embed(
                title="❌ Something went wrong",
                description="The love message could not be scheduled."
            )

            await interaction.followup.send(embed=error_embed)


async def setup(bot):
    await bot.add_cog(LoveCommand(bot))