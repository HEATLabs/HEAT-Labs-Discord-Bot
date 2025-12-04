import discord
from discord.ext import commands
import os
import aiohttp
import json
import traceback
import asyncio
import inspect
from datetime import datetime
from modules.logger import get_logger
from modules.embeds import create_embed, add_embed_footer

logger = get_logger()


class BotMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.webhook_url = os.getenv("WEBHOOK")
        self.session = aiohttp.ClientSession()
        self.command_usage = {}
        self.module_usage = {}
        self.error_stats = {}
        self._ready_sent = False

        if not self.webhook_url:
            logger.warning("WEBHOOK environment variable not set - monitoring disabled")
            self.monitoring_enabled = False
        else:
            self.monitoring_enabled = True
            logger.info("Bot monitoring initialized")

    # Send an embed to the webhook
    async def send_webhook_embed(
        self, title: str, description: str, color: str = "#ff8300", fields: list = None
    ):
        if not self.monitoring_enabled:
            return

        try:
            # Use the standardized create_embed function
            embed = create_embed(
                title=title,
                description=description,
                color=color,
            )

            # Add fields if provided
            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.get("name", "Field"),
                        value=field.get("value", ""),
                        inline=field.get("inline", True),
                    )

            # Add the standardized footer
            embed = add_embed_footer(embed)

            data = {
                "embeds": [embed.to_dict()],
                "username": "HEAT Labs Bot Monitor",
                "avatar_url": "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/assets/public-assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
            }

            async with self.session.post(self.webhook_url, json=data) as response:
                if response.status in (200, 204):
                    logger.debug(f"Monitor webhook sent: {title}")
                else:
                    logger.warning(f"Failed to send webhook: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    # Send embed when bot starts up
    async def on_bot_ready(self):
        if self._ready_sent:
            logger.debug("Bot ready event triggered again, ignoring duplicate")
            return

        self._ready_sent = True

        guild_count = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        command_count = len(self.bot.tree.get_commands())
        cog_count = len(self.bot.cogs)

        description = f"Bot is now online and serving {guild_count} servers"

        fields = [
            {"name": "🖥️ Servers", "value": str(guild_count), "inline": True},
            {"name": "👥 Total Members", "value": str(total_members), "inline": True},
            {
                "name": "📊 Latency",
                "value": f"{round(self.bot.latency * 1000)}ms",
                "inline": True,
            },
            {"name": "⚙️ Commands", "value": str(command_count), "inline": True},
            {"name": "📦 Cogs", "value": str(cog_count), "inline": True},
            {"name": "🔧 Intents", "value": str(self.bot.intents.value), "inline": True},
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Bot Started",
            description=description,
            color="#22C55E",
            fields=fields,
        )

    # Send embed when bot joins a server
    async def on_guild_join(self, guild):
        guild_count = len(self.bot.guilds)

        description = f"Bot joined **{guild.name}**"

        fields = [
            {"name": "🏷️ Server ID", "value": str(guild.id), "inline": True},
            {"name": "👥 Members", "value": str(guild.member_count), "inline": True},
            {"name": "📈 Total Servers", "value": str(guild_count), "inline": True},
            {
                "name": "📅 Created",
                "value": f"<t:{int(guild.created_at.timestamp())}:R>",
                "inline": True,
            },
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Joined Server",
            description=description,
            color="#3B82F6",
            fields=fields,
        )

    # Send embed when bot leaves a server
    async def on_guild_remove(self, guild):
        guild_count = len(self.bot.guilds)

        description = f"Bot left **{guild.name}**"

        fields = [
            {"name": "🏷️ Server ID", "value": str(guild.id), "inline": True},
            {"name": "👥 Members", "value": str(guild.member_count), "inline": True},
            {"name": "📉 Total Servers", "value": str(guild_count), "inline": True},
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Left Server",
            description=description,
            color="#EF4444",
            fields=fields,
        )

    # Monitor command usage
    async def on_app_command_completion(
        self, interaction: discord.Interaction, command: discord.app_commands.Command
    ):
        command_name = command.name
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else "DM"

        # Track command usage
        if command_name not in self.command_usage:
            self.command_usage[command_name] = 0
        self.command_usage[command_name] += 1

        # Track module usage
        cog_name = command.cog.qualified_name if command.cog else "No Cog"
        if cog_name not in self.module_usage:
            self.module_usage[cog_name] = 0
        self.module_usage[cog_name] += 1

        logger.debug(
            f"Command executed: /{command_name} by {interaction.user} in {guild_id}"
        )

    # Send embed when a command error occurs
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        error_type = type(error).__name__

        # Track error statistics
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1

        fields = [
            {
                "name": "💻 Command",
                "value": f"`{ctx.command}`" if ctx.command else "Unknown",
                "inline": True,
            },
            {
                "name": "👤 User",
                "value": f"{ctx.author} ({ctx.author.id})",
                "inline": True,
            },
            {
                "name": "🏷️ Server",
                "value": f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "DM",
                "inline": True,
            },
            {"name": "❌ Error Type", "value": error_type, "inline": False},
            {
                "name": "📝 Error Details",
                "value": f"```{str(error)[:1000]}```",
                "inline": False,
            },
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Command Error",
            description="A command error occurred",
            color="#EF4444",
            fields=fields,
        )

    # Send embed when a command error occurs
    async def on_app_command_error(self, interaction, error):
        error_type = type(error).__name__

        # Track error statistics
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1

        fields = [
            {
                "name": "💻 Command",
                "value": f"`/{interaction.command.name}`"
                if interaction.command
                else "Unknown",
                "inline": True,
            },
            {
                "name": "👤 User",
                "value": f"{interaction.user} ({interaction.user.id})",
                "inline": True,
            },
            {
                "name": "🏷️ Server",
                "value": f"{interaction.guild.name} ({interaction.guild.id})"
                if interaction.guild
                else "DM",
                "inline": True,
            },
            {"name": "❌ Error Type", "value": error_type, "inline": False},
            {
                "name": "📝 Error Details",
                "value": f"```{str(error)[:1000]}```",
                "inline": False,
            },
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Slash Command Error",
            description="An application command error occurred",
            color="#EF4444",
            fields=fields,
        )

    # Monitor HTTP requests from modules
    async def on_http_request(
        self, module_name: str, url: str, status_code: int, response_time: float
    ):
        color = (
            "#10B981"
            if status_code == 200
            else "#F59E0B"
            if status_code < 500
            else "#EF4444"
        )

        fields = [
            {"name": "📦 Module", "value": module_name, "inline": True},
            {
                "name": "🌐 URL",
                "value": f"`{url[:50]}...`" if len(url) > 50 else f"`{url}`",
                "inline": True,
            },
            {"name": "📊 Status", "value": f"HTTP {status_code}", "inline": True},
            {
                "name": "⏱️ Response Time",
                "value": f"{response_time:.2f}ms",
                "inline": True,
            },
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - HTTP Request",
            description="External API request completed",
            color=color,
            fields=fields,
        )

    # Monitor cooldown triggers
    async def on_cooldown_trigger(
        self, user: discord.User, command: str, remaining: float
    ):
        fields = [
            {"name": "👤 User", "value": f"{user} ({user.id})", "inline": True},
            {"name": "💻 Command", "value": f"`/{command}`", "inline": True},
            {"name": "⏰ Remaining", "value": f"{remaining:.1f}s", "inline": True},
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Cooldown Triggered",
            description="User hit command cooldown",
            color="#F59E0B",
            fields=fields,
        )

    # Monitor status rotation
    async def on_status_change(self, old_status: str, new_status: str):
        fields = [
            {"name": "🔄 Old Status", "value": old_status, "inline": True},
            {"name": "🔄 New Status", "value": new_status, "inline": True},
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Status Changed",
            description="Bot status was updated",
            color="#8B5CF6",
            fields=fields,
        )

    # Send periodic statistics
    async def send_periodic_stats(self):
        if not self.monitoring_enabled:
            return

        # Calculate statistics
        total_commands = sum(self.command_usage.values())
        top_commands = sorted(
            self.command_usage.items(), key=lambda x: x[1], reverse=True
        )[:5]
        top_modules = sorted(
            self.module_usage.items(), key=lambda x: x[1], reverse=True
        )[:5]
        error_summary = sorted(
            self.error_stats.items(), key=lambda x: x[1], reverse=True
        )[:5]

        command_stats = "\n".join([f"`/{cmd}`: {count}" for cmd, count in top_commands])
        module_stats = "\n".join([f"`{mod}`: {count}" for mod, count in top_modules])
        error_stats_text = (
            "\n".join([f"`{err}`: {count}" for err, count in error_summary])
            if error_summary
            else "No errors"
        )

        fields = [
            {"name": "📊 Total Commands", "value": str(total_commands), "inline": True},
            {"name": "🖥️ Servers", "value": str(len(self.bot.guilds)), "inline": True},
            {
                "name": "👥 Users",
                "value": str(sum(g.member_count for g in self.bot.guilds)),
                "inline": True,
            },
            {
                "name": "🏆 Top Commands",
                "value": command_stats or "No data",
                "inline": False,
            },
            {
                "name": "📦 Top Modules",
                "value": module_stats or "No data",
                "inline": False,
            },
            {"name": "❌ Recent Errors", "value": error_stats_text, "inline": False},
        ]

        await self.send_webhook_embed(
            title="HEAT Labs - Periodic Statistics",
            description="Bot usage statistics for the current session",
            color="#6366F1",
            fields=fields,
        )

    # Send embed for module-specific errors
    async def on_module_error(
        self, module_name: str, error: Exception, context: str = ""
    ):
        error_type = type(error).__name__

        # Track error statistics
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1

        fields = [
            {"name": "📦 Module", "value": module_name, "inline": True},
            {"name": "❌ Error Type", "value": error_type, "inline": True},
            {
                "name": "📝 Error Details",
                "value": f"```{str(error)[:1000]}```",
                "inline": False,
            },
        ]

        if context:
            fields.insert(1, {"name": "🔍 Context", "value": context, "inline": True})

        await self.send_webhook_embed(
            title="HEAT Labs - Module Error",
            description="A module error occurred",
            color="#F59E0B",
            fields=fields,
        )

    # Send embed for status rotation errors
    async def on_status_rotation_error(self, error: Exception):
        await self.on_module_error("StatusRotator", error, "Status Rotation")

    # Send embed for server tracker errors
    async def on_server_tracker_error(self, error: Exception):
        await self.on_module_error("ServerTracker", error, "Server Tracking")

    # Close the session when cog unloads
    def cog_unload(self):
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("Monitor unloaded")


async def setup(bot: commands.Bot) -> None:
    # Check if monitor is already loaded
    if hasattr(bot, "monitor"):
        logger.info("Monitor already loaded, skipping duplicate setup")
        return

    monitor = BotMonitor(bot)

    # Add event listeners for comprehensive monitoring
    bot.add_listener(monitor.on_bot_ready, "on_ready")
    bot.add_listener(monitor.on_guild_join, "on_guild_join")
    bot.add_listener(monitor.on_guild_remove, "on_guild_remove")
    bot.add_listener(monitor.on_command_error, "on_command_error")
    bot.add_listener(monitor.on_app_command_error, "on_app_command_error")
    bot.add_listener(monitor.on_app_command_completion, "on_app_command_completion")

    # Store monitor instance on bot for access from other modules
    bot.monitor = monitor

    # Start periodic stats task
    async def periodic_stats():
        await asyncio.sleep(60)  # Wait 1 minute after startup
        while True:
            await asyncio.sleep(3600)  # Every hour
            await monitor.send_periodic_stats()

    bot.loop.create_task(periodic_stats())

    logger.info(
        "Monitor loaded - monitoring enabled"
        if monitor.monitoring_enabled
        else "Monitor loaded - monitoring disabled"
    )
