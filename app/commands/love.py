import os
import asyncio

import discord

from datetime import datetime
from apscheduler.triggers.date import DateTrigger
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pytz import timezone


load_dotenv()

CHANNEL_ID = os.getenv("CHANNEL_ID")
USER_ID = os.getenv("USER_ID")
USER_MAX_ID = os.getenv("USER_MAX_ID")

TALLINN_TZ = timezone("Europe/Tallinn")


class LoveCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_love_message(self, recipient_id=None):
        try:
            print(
                f"[LOVE] Sending scheduled message "
                f"to {recipient_id}"
            )

            channel_id = int(CHANNEL_ID)

            channel = self.bot.get_channel(channel_id)

            if channel is None:
                print(
                    f"[LOVE] Channel {channel_id} not cached. "
                    "Fetching from Discord..."
                )

                channel = await self.bot.fetch_channel(
                    channel_id
                )

            if recipient_id:
                await channel.send(
                    f"<@{recipient_id}> :point_right:, "
                    "I love you :open_hands: this much "
                    ":pinching_hand: ❤️"
                )
            else:
                await channel.send(
                    "Sending love to everyone! :heart:"
                )

            print(
                f"[LOVE] Message sent to "
                f"#{channel.name} ({channel.id})."
            )

        except discord.NotFound:
            print(
                f"[LOVE] Channel does not exist: "
                f"{CHANNEL_ID}"
            )

        except discord.Forbidden:
            print(
                f"[LOVE] Bot has no permission to access/send "
                f"to channel: {CHANNEL_ID}"
            )

        except Exception as e:
            print(
                f"[LOVE] Error in send_love_message: {e}"
            )

    @app_commands.command(
        name="love",
        description=(
            "Schedules a love message. "
            "Type the command and follow the prompt."
        )
    )
    async def love(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Please enter the hour (0-23) "
            "to schedule the love message:"
        )

        def check_hour(msg):
            return (
                msg.author == interaction.user
                and msg.channel == interaction.channel
                and msg.content.isdigit()
                and 0 <= int(msg.content) <= 23
            )

        try:
            hour_msg = await self.bot.wait_for(
                "message",
                check=check_hour,
                timeout=30.0
            )

            hour = int(hour_msg.content)

            await interaction.followup.send(
                "Please enter the minutes (0-59):"
            )

            def check_minutes(msg):
                return (
                    msg.author == interaction.user
                    and msg.channel == interaction.channel
                    and msg.content.isdigit()
                    and 0 <= int(msg.content) <= 59
                )

            minutes_msg = await self.bot.wait_for(
                "message",
                check=check_minutes,
                timeout=30.0
            )

            minutes = int(minutes_msg.content)

            sender_id = interaction.user.id

            recipient_id = (
                USER_ID
                if str(sender_id) == USER_MAX_ID
                else USER_MAX_ID
            )

            now = datetime.now(TALLINN_TZ)

            run_time = now.replace(
                hour=hour,
                minute=minutes,
                second=0,
                microsecond=0
            )

            # If that time already passed today,
            # schedule it for tomorrow.
            if run_time <= now:
                run_time = run_time.replace(
                    day=now.day
                )

                from datetime import timedelta
                run_time += timedelta(days=1)

            scheduler = self.bot.scheduler

            scheduler.add_job(
                self.send_love_message,
                DateTrigger(
                    run_date=run_time
                ),
                args=[recipient_id],
                id=(
                    f"love_message_"
                    f"{interaction.user.id}_"
                    f"{recipient_id}_"
                    f"{run_time.timestamp()}"
                )
            )

            await interaction.followup.send(
                f"Love message scheduled for "
                f"{run_time:%H:%M} "
                f"to <@{recipient_id}>."
            )

            print(
                f"[LOVE] Job scheduled: "
                f"{run_time.isoformat()}"
            )

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "You didn't respond in time, "
                "please try the command again."
            )

        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {e}"
            )


async def setup(bot):
    await bot.add_cog(
        LoveCommand(bot)
    )