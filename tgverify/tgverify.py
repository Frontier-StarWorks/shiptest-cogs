# Standard Imports
import logging
from typing import Union

# Discord Imports
import discord

# Redbot Imports
from redbot.core import commands, checks, Config, app_commands

from tgcommon.errors import TGRecoverableError, TGUnrecoverableError
from tgcommon.util import normalise_to_ckey
from typing import cast

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_tgverify")

BaseCog = getattr(commands, "Cog", object)


class TGverify(BaseCog):
    """
    Connector that will integrate with any database using the latest tg schema, provides utility functionality
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.visible_config = [
            "min_living_minutes",
            "verified_role",
            "instructions_link",
            "welcomegreeting",
            "disabledgreeting",
            "bunkerwarning",
            "bunker",
            "welcomechannel",
        ]

        default_guild = {
            "min_living_minutes": 60,
            "verified_role": None,
            "verified_living_role": None,
            "instructions_link": "",
            "welcomegreeting": "",
            "disabledgreeting": "",
            "bunkerwarning": "",
            "bunker": False,
            "disabled": False,
            "welcomechannel": "",
        }

        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.hybrid_group()
    @checks.mod_or_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def tgverify(self, ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @commands.guild_only()
    @tgverify.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self, ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.guild(ctx.guild).all()
        embed = discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:", value=v, inline=False)
            else:
                embed.add_field(name=f"{k}:", value="`redacted`", inline=False)
        await ctx.send(embed=embed)

    @config.command()
    async def living_minutes(self, ctx, min_living_minutes: int = None):
        """
        Sets the minimum required living minutes before this bot will apply a verification role to a user
        """
        try:
            if min_living_minutes is None:
                await self.config.guild(ctx.guild).min_living_minutes.set(0)
                await ctx.send(
                    f"Minimum living minutes required for verification removed!"
                )
            else:
                await self.config.guild(ctx.guild).min_living_minutes.set(
                    min_living_minutes
                )
                await ctx.send(
                    f"Minimum living minutes required for verification set to: `{min_living_minutes}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send(
                "There was a problem setting the minimum required living minutes"
            )

    @config.command()
    async def instructions_link(self, ctx, instruction_link: str):
        """
        Sets the link to further instructions on how to generate verification information
        """
        try:
            await self.config.guild(ctx.guild).instructions_link.set(instruction_link)
            await ctx.send(f"Instruction link set to: `{instruction_link}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the instructions link")

    @config.command()
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        Sets the channel to send the welcome message
        If channel isn"t specified, the guild's default channel will be used
        """
        guild = ctx.message.guild
        guild_settings = await self.config.guild(guild).welcomechannel()
        if channel is None:
            channel = ctx.message.channel
        if not channel.permissions_for(ctx.me).send_messages:
            msg = "I do not have permissions to send messages to {channel}".format(
                channel=channel.mention
            )
            await ctx.send(msg)
            return
        guild_settings = channel.id
        await self.config.guild(guild).welcomechannel.set(guild_settings)
        msg = "I will now send welcome messages to {channel}".format(
            channel=channel.mention
        )
        await channel.send(msg)

    @config.command()
    async def welcome_greeting(self, ctx, welcomegreeting: str):
        """
        Sets the welcoming greeting
        """
        try:
            await self.config.guild(ctx.guild).welcomegreeting.set(welcomegreeting)
            await ctx.send(f"Welcome greeting set to: `{welcomegreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the Welcome greeting")

    @config.command()
    async def disabled_greeting(self, ctx, disabledgreeting: str):
        """
        Sets the welcoming greeting when the verification system is disabled
        """
        try:
            await self.config.guild(ctx.guild).disabledgreeting.set(disabledgreeting)
            await ctx.send(f"Disabled greeting set to: `{disabledgreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the disabled greeting")

    @config.command()
    async def bunker_warning(self, ctx, bunkerwarning: str):
        """
        Sets the additional message added to the greeting message when the bunker is on
        """
        try:
            await self.config.guild(ctx.guild).bunkerwarning.set(bunkerwarning)
            await ctx.send(f"Bunker warning set to: `{bunkerwarning}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the bunker warning")

    @tgverify.command()
    async def bunker(self, ctx):
        """
        Toggle bunker status on or off
        """
        try:
            bunker = await self.config.guild(ctx.guild).bunker()
            bunker = not bunker
            await self.config.guild(ctx.guild).bunker.set(bunker)
            if bunker:
                await ctx.send(f"The bunker warning is now on")
            else:
                await ctx.send(f"The bunker warning is now off")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem toggling the bunker")

    @tgverify.command()
    async def broken(self, ctx):
        """
        For when verification breaks
        """
        try:
            disabled = await self.config.guild(ctx.guild).disabled()
            disabled = not disabled
            await self.config.guild(ctx.guild).disabled.set(disabled)
            if disabled:
                await ctx.send(f"The verification system is now off")
            else:
                await ctx.send(f"The verification system is now on")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem toggling the disabled flag")

    @config.command()
    async def verified_role(self, ctx, verified_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_role)
            if not role:
                return await ctx.send(f"This is not a valid role for this discord!")
            if verified_role is None:
                await self.config.guild(ctx.guild).verified_role.set(None)
                await ctx.send(f"No role will be set when the user verifies!")
            else:
                await self.config.guild(ctx.guild).verified_role.set(verified_role)
                await ctx.send(
                    f"When a user meets minimum verification this role will be applied: `{verified_role}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the verified role")

    @config.command()
    async def verified_living_role(self, ctx, verified_living_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_living_role)
            if not role:
                return await ctx.send(f"This is not a valid role for this discord!")
            if verified_living_role is None:
                await self.config.guild(ctx.guild).verified_living_role.set(None)
                await ctx.send(f"No role will be set when the user verifies!")
            else:
                await self.config.guild(ctx.guild).verified_living_role.set(
                    verified_living_role
                )
                await ctx.send(
                    f"When a user meets minimum verification this role will be applied: `{verified_living_role}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the verified role")

    @tgverify.command()
    async def discords(self, ctx, ckey: str):
        """
        List all past discord accounts this ckey has verified with
        """
        tgdb = self.get_tgdb()
        ckey = normalise_to_ckey(ckey)
        message = await ctx.send("Collecting discord accounts for ckey....")

        embed = discord.Embed(color=await ctx.embed_color())
        embed.set_author(
            name=f"Discord accounts historically linked to {str(ckey).title()}"
        )
        links = await tgdb.all_discord_links_for_ckey(ctx, ckey)
        if len(links) <= 0:
            return await message.edit(
                content="No discord accounts found for this ckey"
            )

        names = ""
        for link in links:
            names += f"User linked <@{link.discord_id}> on {link.timestamp}, current account: {link.validity}\n"

        embed.add_field(name="__Discord accounts__", value=names, inline=False)
        await message.edit(content=None, embed=embed)

    @tgverify.command()
    async def whois(self, ctx, discord_user: discord.User):
        """
        Return the ckey attached to the given discord user, if they have one
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Finding out the ckey of user....")
        # Attempt to find the discord ids based on the one time token passed in.
        discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
        if discord_link:
            message = await message.edit(
                content=f"This discord user is linked to the ckey {discord_link.ckey}"
            )
        else:
            message = await message.edit(
                content=f"This discord user has no ckey linked"
            )

    @tgverify.command()
    async def deverify(self, ctx, discord_user: discord.User):
        """
        Deverifies the ckey linked to this user.
        
        All historical verifications will be removed, the user will have to connect to the game
        and generate a new one time token to get their verification role
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Finding out the ckey of user....")

        # Attempt to find the discord link from the user
        discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
        if discord_link:
            # now clear all the links for this ckey
            await tgdb.clear_all_valid_discord_links_for_ckey(
                ctx, discord_link.ckey
            )
            member = ctx.guild.get_member(discord_user.id)
            role = await self.config.guild(ctx.guild).verified_role()
            role = ctx.guild.get_role(role)
            if(role):
                await member.remove_roles(role, reason="User has been deverified")

            message = await message.edit(content=f"User has been deverified")
        else:
            message = await message.edit(
                content=f"This discord user has no ckey linked"
            )

    @commands.guild_only()
    @commands.hybrid_command()
    @checks.mod_or_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_verify(self, ctx, discord_user: discord.User, ckey: str):
        """
        Forcefully verifies a discord user as a specified ckey. Admin only.
        """
        message = await ctx.send("Verifying...")

        tgdb = self.get_tgdb()
        discord_member: discord.Member = ctx.guild.get_member(discord_user.id)
        role = await self.config.guild(ctx.guild).verified_role()
        role = ctx.guild.get_role(role)

        if not role:
            raise TGUnrecoverableError(
                "No verification role is configured, configure it with the config command"
            )

        await tgdb.add_discord_link(ctx, ckey, discord_user.id)

        if(role):
            await discord_member.add_roles(role, reason="User has been manually verified")

        return await message.edit(content=f"User {discord_user.name} manually verified as {ckey}.")

    # Now the only user facing command, so this has rate limiting across the sky
    @commands.cooldown(2, 60, type=commands.BucketType.user)
    @commands.cooldown(6, 60, type=commands.BucketType.guild)
    @commands.max_concurrency(3, per=commands.BucketType.guild, wait=False)
    @commands.guild_only()
    @commands.command()
    async def verify(self, ctx: commands.context, *, one_time_token: str = None):
        """
        Attempt to verify the user, based on the passed in one time code.
        
        This command is rated limited to two attempts per user every 60 seconds, and 6 attempts per entire discord every 60 seconds
        """
        # Get the minimum required living minutes
        min_required_living_minutes = await self.config.guild(
            ctx.guild
        ).min_living_minutes()
        instructions_link = await self.config.guild(ctx.guild).instructions_link()
        role = await self.config.guild(ctx.guild).verified_role()
        verified_role = await self.config.guild(ctx.guild).verified_living_role()
        role = ctx.guild.get_role(role)
        verified_role = ctx.guild.get_role(verified_role)
        tgdb = self.get_tgdb()
        ckey = None

        # First lets try to remove their message, since the one time token is technically a secret if something goes wrong
        try:
            await ctx.message.delete()
        except (discord.DiscordException):
            await ctx.send(
                "I do not have the required permissions to delete messages, please remove/edit the one time token manually."
            )
        if not role:
            raise TGUnrecoverableError(
                "No verification role is configured, configure it with the config command"
            )
        if not verified_role:
            raise TGUnrecoverableError(
                "No verification role is configured for living minutes, configure it with config command"
            )

        if await tgdb.discord_link_for_discord_id(ctx, ctx.author.id):
            return await ctx.send("You are already verified")

        message = await ctx.send("Attempting to verify you....")

        if one_time_token:
            # Attempt to find the user based on the one time token passed in.
            ckey = await tgdb.lookup_ckey_by_token(ctx, one_time_token)

        prexisting = False
        # they haven't specified a one time token or it didn't match, see if we already have a linked ckey for the user id that is still valid
        if ckey is None:
            discord_link = await tgdb.discord_link_for_discord_id(
                ctx, ctx.author.id
            )
            if discord_link and discord_link.valid > 0:
                prexisting = True
                ckey = discord_link.ckey
                # Now look for the user based on the ckey
                # player = await tgdb.get_player_by_ckey(ctx, discord_link.ckey)
                # if player and player['living_time'] >= min_required_living_minutes:
                #    await ctx.author.add_roles(verified_role, reason="User has verified against their in game living minutes")
                # we have a fast path, just reapply the linked role and bail
                # await ctx.author.add_roles(role, reason="User has verified in game")
                # return await message.edit(content=f"Congrats {ctx.author} your verification is complete")
            else:
                raise TGRecoverableError(
                    f"Sorry {ctx.author} it looks like you don't have a ckey linked to this discord account, go back into game and try generating another! See {instructions_link} for more information. \n\nIf it's still failing after a few tries, ask for support from the verification team, "
                )

        log.info(
            f"Verification request by {ctx.author.id}, for ckey {ckey}, token was: {one_time_token}"
        )
        # Now look for the user based on the ckey
        player = await tgdb.get_player_by_ckey(ctx, ckey)

        if player is None:
            raise TGRecoverableError(
                f"Sorry {ctx.author} looks like we couldn't look up your user, ask the verification team for support!"
            )

        if not prexisting:
            # clear any/all previous valid links for ckey or the discord id (in case they have decided to make a new ckey)
            await tgdb.clear_all_valid_discord_links_for_ckey(ctx, ckey)
            await tgdb.clear_all_valid_discord_links_for_discord_id(
                ctx, ctx.author.id
            )
            # Record that the user is linked against a discord id
            await tgdb.update_discord_link(ctx, one_time_token, ctx.author.id)

        successful = False
        if role:
            await ctx.author.add_roles(role, reason="User has verified in game")
        if player["living_time"] >= min_required_living_minutes:
            successful = True
            await ctx.author.add_roles(
                verified_role,
                reason="User has verified against their in game living minutes",
            )

        fuck = f"Congrats {ctx.author} your verification is complete, but you do not have {min_required_living_minutes} minutes in game as a living crew member (you have {player['living_time']}), so you may not have access to all channels. You can always verify again later by simply doing `?verify` and if you have enough minutes, you will gain access to the remaining channels"
        if successful:
            fuck = f"Congrats {ctx.author} your verification is complete"
        return await message.edit(content=fuck)

    @app_commands.command(name="verify")
    @app_commands.guild_only()
    async def verify_slash(self, interaction: discord.Interaction, one_time_token: str = None):
        """
        Attempt to verify the user, based on the passed in one time code.
        
        This command is rated limited to two attempts per user every 60 seconds, and 6 attempts per entire discord every 60 seconds
        """
        # Get the minimum required living minutes
        min_required_living_minutes = await self.config.guild(
            interaction.guild
        ).min_living_minutes()
        instructions_link = await self.config.guild(interaction.guild).instructions_link()
        role = await self.config.guild(interaction.guild).verified_role()
        verified_role = await self.config.guild(interaction.guild).verified_living_role()
        role = interaction.guild.get_role(role)
        verified_role = interaction.guild.get_role(verified_role)
        tgdb = self.get_tgdb()
        ckey = None

        if not role:
            raise TGUnrecoverableError(
                "No verification role is configured, configure it with the config command"
            )
        if not verified_role:
            raise TGUnrecoverableError(
                "No verification role is configured for living minutes, configure it with config command"
            )

        if await tgdb.discord_link_for_discord_id(interaction, interaction.user.id):
            return await interaction.response.send_message("You are already verified!", ephemeral=True)

        await interaction.response.send_message("Attempting to verify you...", ephemeral=True)

        if one_time_token:
            # Attempt to find the user based on the one time token passed in.
            ckey = await tgdb.lookup_ckey_by_token(interaction, one_time_token)

        prexisting = False
        # they haven't specified a one time token or it didn't match, see if we already have a linked ckey for the user id that is still valid
        if ckey is None:
            discord_link = await tgdb.discord_link_for_discord_id(
                interaction, interaction.user.id
            )
            if discord_link and discord_link.valid > 0:
                prexisting = True
                ckey = discord_link.ckey
                # Now look for the user based on the ckey
                # player = await tgdb.get_player_by_ckey(ctx, discord_link.ckey)
                # if player and player['living_time'] >= min_required_living_minutes:
                #    await ctx.author.add_roles(verified_role, reason="User has verified against their in game living minutes")
                # we have a fast path, just reapply the linked role and bail
                # await ctx.author.add_roles(role, reason="User has verified in game")
                # return await message.edit(content=f"Congrats {ctx.author} your verification is complete")
            else:
                return await interaction.edit_original_response(
                    content=f"Sorry {interaction.user.name} it looks like you don't have a ckey linked to this discord account, go back into game and try generating another! See {instructions_link} for more information. \n\nIf it's still failing after a few tries, ask for support from the verification team."
                )

        log.info(
            f"Verification request by {interaction.user.id}, for ckey {ckey}, token was: {one_time_token}"
        )
        # Now look for the user based on the ckey
        player = await tgdb.get_player_by_ckey(interaction, ckey)

        if player is None:
            return await interaction.edit_original_response(
                content=f"Sorry {interaction.user.name} looks like we couldn't look up your user, ask the verification team for support!"
            )

        if not prexisting:
            # clear any/all previous valid links for ckey or the discord id (in case they have decided to make a new ckey)
            await tgdb.clear_all_valid_discord_links_for_ckey(interaction, ckey)
            await tgdb.clear_all_valid_discord_links_for_discord_id(
                interaction, interaction.user.id
            )
            # Record that the user is linked against a discord id
            await tgdb.update_discord_link(interaction, one_time_token, interaction.user.id)

        successful = False
        if role:
            await interaction.user.add_roles(role, reason="User has verified in game")
        if player["living_time"] >= min_required_living_minutes:
            successful = True
            await interaction.user.add_roles(
                verified_role,
                reason="User has verified against their in game living minutes",
            )

        if successful:
            return await interaction.edit_original_response(content=f"Congrats {interaction.user.name} your verification is complete")
        
        return await interaction.edit_original_response(
            content=f"Congrats {interaction.user.name} your verification is complete, but you do not have {min_required_living_minutes} minutes in game as a living crew member (you have {player['living_time']}), so you may not have access to all channels. You can always verify again later by simply doing `?verify` and if you have enough minutes, you will gain access to the remaining channels"
        )
    
    @tgverify.command()
    async def test(self, ctx, discord_user: discord.User):
        """
        Test welcome message sending
        """
        guild = ctx.guild
        member = guild.get_member(discord_user.id)
        await self.handle_member_join(member)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.handle_member_join(member)

    async def handle_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        channel_id = await self.config.guild(guild).welcomechannel()
        channel = cast(discord.TextChannel, guild.get_channel(channel_id))
        if channel is None:
            log.info(
                f"tgverify channel not found for guild, it was probably deleted User joined: {member}"
            )
            return

        if not guild.me.permissions_in(channel).send_messages:
            log.info(f"Permissions Error. User that joined:{member}")
            log.info(
                f"Bot doesn't have permissions to send messages to {guild.name}'s #{channel.name} channel"
            )
            return

        final = ""
        if await self.config.guild(guild).disabled():
            msg = await self.config.guild(guild).disabledgreeting()
            final = msg.format(member, guild)
        else:
            msg = await self.config.guild(guild).welcomegreeting()
            final = msg.format(member, guild)
        bunkermsg = await self.config.guild(guild).bunkerwarning()
        bunker = await self.config.guild(guild).bunker()
        if bunkermsg != "" and bunker:
            final = final + " " + bunkermsg

        await channel.send(final)

    def get_tgdb(self):
        tgdb = self.bot.get_cog("TGDB")
        if not tgdb:
            raise TGUnrecoverableError(
                "TGDB must exist and be configured for tgverify cog to work"
            )

        return tgdb
