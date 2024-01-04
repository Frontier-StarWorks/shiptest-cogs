import asyncio
import time
from datetime import datetime
import logging
from math import floor

import discord

from redbot.core import commands, checks, Config, app_commands

__version__ = "1.0.0"
__author__ = "MarkSuckerberg"

log = logging.getLogger("red.SS13Status")

UNIX_DAYS = 60 * 60 * 24
BYOND_EPOCH = datetime(2000, 1, 1, 0, 0, 0, 0).timestamp()
MONTH_NAMES = {
    0: "January",
    1: "February",
    2: "March",
    3: "April",
    4: "May",
    5: "June",
    6: "Sol",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
    13: "Year Day"
}

class FSCTime(commands.Cog):

    def __init__(self, bot):
        self.time_loop = None

        self.bot = bot
        self.config = Config.get_conf(self, 3047293194, force_registration=True)

        default_guild = {
            "message_id": None,
            "channel_id": None,
        }

        self.config.register_guild(**default_guild)
        self.time_loop = bot.loop.create_task(self.time_update_loop())
    
    def cog_unload(self):
        self.time_loop.cancel()

    @commands.hybrid_command()
    async def fsctime(self, ctx):
        """
        Displays the current time in FSC
        """
        await ctx.send(content=None, embed=self.generate_embed())

    @commands.guild_only()
    @commands.hybrid_group()
    @checks.admin_or_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def setfsctime(self, ctx):
        """
        Configuration group for the SS13 status command
        """
        pass

    @fsctime.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """
        Sets the channel to post the time in
        """
        cfg = self.config.guild(ctx.guild)
        
        message = await channel.send(content=None, embed=self.generate_embed())
        await cfg.message_id.set(message.id)

        await cfg.channel_id.set(channel.id)
        await ctx.send("Channel set!")

    @fsctime.command()
    async def setmessage(self, ctx, message: discord.Message):
        """
        Sets the message to update
        """
        cfg = self.config.guild(ctx.guild)
        await cfg.message_id.set(message.id)
        await ctx.send("Message set!")

    @fsctime.command()
    async def current(self, ctx):
        """
        Shows the current settings
        """
        cfg = self.config.guild(ctx.guild)
        message = await cfg.message_id()
        channel = await cfg.channel_id()
        await ctx.send(f"Channel: {channel}\nMessage: {message}")

    async def time_update_loop(self):
        while self == self.bot.get_cog("FSCTime"):
            for guild in self.bot.guilds:
                cfg = self.config.guild(guild)

                message = await cfg.message_id()
                channel = await cfg.channel_id()
                cached: discord.Message

                if(channel == None):
                    continue

                if(message == None):
                    if(isinstance(message, str)): 
                        message = int(message)
                    cached = await channel.send("caching initial context")
                    await cfg.message_id.set(cached.id)
                else:
                    try:
                        cached = await channel.fetch_message(message)
                    except(discord.NotFound):
                        cached = await channel.send("caching initial context")
                        await cfg.message_id.set(cached.id)

                await cached.edit(content=None, embed=self.generate_embed())

            await asyncio.sleep(60)

    def generate_embed(self):
        embed = discord.Embed(title="Current Sector Time", description=f"{datetime.utcnow().strftime('%H:%M')} {self.get_date()}")
        return embed

    def get_date(self):
        timestamp = datetime.utcnow().timestamp() - BYOND_EPOCH #I hate this
        days = floor(timestamp / UNIX_DAYS)
        years = floor(days / 365) + 481

        day_of_year = days % 365 + 1
        month_of_year = floor(day_of_year / 28)

        day_of_month = day_of_year % 28 + 1
        month_name = MONTH_NAMES[month_of_year]

        return f"{month_name} {day_of_month}, {years} FSC"
