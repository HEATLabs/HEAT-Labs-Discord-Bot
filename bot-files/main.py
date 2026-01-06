import discord
from discord.ext import commands
import os
import asyncio
import traceback
from dotenv import load_dotenv
from modules.logger import get_logger
from modules.cooldown import global_cooldown
from modules.embeds import create_embed, add_embed_footer

# Load environment variables
load_dotenv()

# Get logger instance
logger = get_logger()


class ShardMonitor:
    def __init__(self):
        self.webhook_url = os.getenv("SHARD_WEBHOOK")
        self.session = None
        self.last_embed_time = {}

        if not self.webhook_url:
            logger.warning(
                "SHARD_WEBHOOK environment variable not set - shard monitoring disabled"
            )
            self.monitoring_enabled = False
        else:
            self.monitoring_enabled = True
            logger.info("Shard monitor initialized")

    async def initialize(self):
        if self.monitoring_enabled:
            import aiohttp

            self.session = aiohttp.ClientSession()

    async def send_shard_embed(
        self,
        title: str,
        description: str,
        color: int,
        shard_id: int,
        fields: list = None,
        is_summary: bool = False,
    ):
        if not self.monitoring_enabled or not self.session:
            return

        # 1 second delay between embeds for the same shard
        current_time = asyncio.get_event_loop().time()
        if shard_id in self.last_embed_time:
            time_since_last = current_time - self.last_embed_time[shard_id]
            if time_since_last < 1.0:
                await asyncio.sleep(1.0 - time_since_last)

        self.last_embed_time[shard_id] = asyncio.get_event_loop().time()

        try:
            # Create embed
            if is_summary:
                embed_title = title
            else:
                embed_title = f"Shard {shard_id} - {title}"

            embed = discord.Embed(
                title=embed_title,
                description=description,
                color=color,
            )

            # Add shard-specific field
            if not is_summary:
                embed.add_field(name="🆔 Shard ID", value=str(shard_id), inline=True)

            # Add any additional fields
            if fields:
                for field in fields:
                    embed.add_field(
                        name=field["name"],
                        value=field["value"],
                        inline=field.get("inline", True),
                    )

            # Add standardized footer
            embed = add_embed_footer(embed)

            # Prepare webhook data
            data = {
                "embeds": [embed.to_dict()],
                "username": "HEAT Labs Shard Monitor",
                "avatar_url": "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/assets/public-assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
            }

            # Send to webhook
            async with self.session.post(self.webhook_url, json=data) as response:
                if response.status in (200, 204):
                    logger.debug(f"Shard webhook sent: {title} for shard {shard_id}")
                else:
                    logger.warning(
                        f"Failed to send shard webhook: HTTP {response.status}"
                    )

        except Exception as e:
            logger.error(f"Error sending shard webhook: {e}")

    async def close(self):
        if self.session:
            await self.session.close()


class HEATLabsBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            shard_count=None,
        )

        # Check global cooldown
        self.tree.interaction_check = global_cooldown.interaction_check

        # Initialize shard monitor
        self.shard_monitor = ShardMonitor()

        # Hourly update task
        self.hourly_update_task = None

        logger.info("HEAT Labs Bot initialized with automatic sharding")

    # Load all command modules
    async def setup_hook(self):
        # Initialize shard monitor session
        await self.shard_monitor.initialize()

        # Start hourly update task
        self.hourly_update_task = asyncio.create_task(self.hourly_member_count_update())

        loaded = []
        failed = []

        # Load monitor first
        try:
            await self.load_extension("modules.monitor")
            loaded.append("modules.monitor")
            logger.info("Successfully loaded: modules.monitor")
        except Exception as e:
            logger.error(f"Failed to load modules.monitor: {e}")
            failed.append(("modules.monitor", str(e)))

        # Load other command modules
        for filename in os.listdir("./commands"):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"commands.{filename[:-3]}"
                try:
                    await self.load_extension(module_name)
                    loaded.append(module_name)
                    logger.info(f"Successfully loaded: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load {module_name}: {e}")
                    failed.append((module_name, str(e)))

        await self.tree.sync()
        logger.info(
            f"Commands synced with Discord ({len(loaded)} loaded, {len(failed)} failed)"
        )

    # Task to update member counts every hour
    async def hourly_member_count_update(self):
        await asyncio.sleep(3600)

        while True:
            try:
                logger.info("Starting hourly member count update...")

                from modules.servers import ServerTracker

                tracker = ServerTracker()

                # Update all member counts
                updated_count = tracker.update_all_member_counts(self.guilds)

                logger.info(
                    f"Hourly member count update complete: {updated_count} servers updated"
                )

                # Log total members
                total_members = tracker.get_total_members()
                logger.info(
                    f"Total tracked members across all servers: {total_members}"
                )

                # Send periodic statistics through monitor if available
                if hasattr(self, "monitor"):
                    await self.monitor.send_periodic_stats()

            except Exception as e:
                logger.error(f"Error during hourly member count update: {e}")
                # Send error to monitor if available
                if hasattr(self, "monitor"):
                    await self.monitor.on_server_tracker_error(e)

            # Wait for 1 hour before next update
            await asyncio.sleep(3600)

    async def on_ready(self):
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Shard count: {self.shard_count}")
        logger.info(
            f"Bot is serving {len(self.guilds)} guilds across {len(self.shards)} shards"
        )

        # Send shard ready summary
        if self.shard_monitor.monitoring_enabled:
            shard_info = []
            for shard_id, shard in self.shards.items():
                guild_count = len([g for g in self.guilds if g.shard_id == shard_id])
                shard_info.append(f"Shard {shard_id}: {guild_count} guilds")

            description = f"All {len(self.shards)} shards are now connected and ready"
            fields = [
                {
                    "name": "🖥️ Total Guilds",
                    "value": str(len(self.guilds)),
                    "inline": True,
                },
                {
                    "name": "🔢 Shard Count",
                    "value": str(self.shard_count),
                    "inline": True,
                },
                {
                    "name": "📊 Latency",
                    "value": f"{round(self.latency * 1000)}ms",
                    "inline": True,
                },
                {
                    "name": "📈 Shard Distribution",
                    "value": "\n".join(shard_info),
                    "inline": False,
                },
            ]

            await self.shard_monitor.send_shard_embed(
                title="✅ All Shards Ready",
                description=description,
                color=0x22C55E,
                shard_id=0,
                fields=fields,
                is_summary=True,
            )

        # Sync servers with the servers.json file
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.sync_servers(self.guilds)
            logger.info("Server sync completed successfully")

            # Log total members from tracker
            total_members = tracker.get_total_members()
            logger.info(f"Total tracked members across all servers: {total_members}")

        except Exception as e:
            logger.error(f"Error during server sync: {e}")
            # Send to monitor if available
            if hasattr(self, "monitor"):
                await self.monitor.on_server_tracker_error(e)

        # Start status rotation task
        try:
            from modules.status import StatusRotator

            self.status_rotator = StatusRotator(self)
            await self.status_rotator.start_rotation()
            logger.info("Status rotation started")
        except Exception as e:
            logger.error(f"Error starting status rotation: {e}")
            # Send to monitor if available
            if hasattr(self, "monitor"):
                await self.monitor.on_status_rotation_error(e)

        # Notify monitor that bot is ready
        if hasattr(self, "monitor"):
            await self.monitor.on_bot_ready()

    # Shard connection events
    async def on_shard_connect(self, shard_id):
        logger.info(f"Shard {shard_id} connected to Discord")

        if self.shard_monitor.monitoring_enabled:
            description = f"Shard {shard_id} has successfully connected to Discord"
            fields = [
                {
                    "name": "📊 Latency",
                    "value": f"{round(self.latency * 1000)}ms",
                    "inline": True,
                },
                {"name": "🔌 Status", "value": "Connected", "inline": True},
            ]

            await self.shard_monitor.send_shard_embed(
                title="🔌 Shard Connected",
                description=description,
                color=0x10B981,
                shard_id=shard_id,
                fields=fields,
            )

    async def on_shard_disconnect(self, shard_id):
        logger.warning(f"Shard {shard_id} disconnected from Discord")

        if self.shard_monitor.monitoring_enabled:
            description = f"Shard {shard_id} has disconnected from Discord"
            fields = [
                {"name": "🔌 Status", "value": "Disconnected", "inline": True},
                {
                    "name": "⚠️ Action",
                    "value": "Attempting to reconnect...",
                    "inline": True,
                },
            ]

            await self.shard_monitor.send_shard_embed(
                title="🔌 Shard Disconnected",
                description=description,
                color=0xF59E0B,
                shard_id=shard_id,
                fields=fields,
            )

    async def on_shard_ready(self, shard_id):
        shard_guilds = [g for g in self.guilds if g.shard_id == shard_id]
        logger.info(f"Shard {shard_id} is ready - serving {len(shard_guilds)} guilds")

        if self.shard_monitor.monitoring_enabled:
            description = f"Shard {shard_id} is now ready and operational"
            fields = [
                {
                    "name": "🏢 Guilds Served",
                    "value": str(len(shard_guilds)),
                    "inline": True,
                },
                {
                    "name": "👥 Members",
                    "value": str(sum(g.member_count for g in shard_guilds)),
                    "inline": True,
                },
                {"name": "🔌 Status", "value": "Ready", "inline": True},
            ]

            await self.shard_monitor.send_shard_embed(
                title="✅ Shard Ready",
                description=description,
                color=0x22C55E,
                shard_id=shard_id,
                fields=fields,
            )

    async def on_shard_resumed(self, shard_id):
        logger.info(f"Shard {shard_id} resumed session")

        if self.shard_monitor.monitoring_enabled:
            description = f"Shard {shard_id} has resumed its session"
            fields = [
                {"name": "🔌 Status", "value": "Resumed", "inline": True},
                {
                    "name": "📊 Latency",
                    "value": f"{round(self.latency * 1000)}ms",
                    "inline": True,
                },
            ]

            await self.shard_monitor.send_shard_embed(
                title="🔄 Shard Resumed",
                description=description,
                color=0x3B82F6,
                shard_id=shard_id,
                fields=fields,
            )

    # Error handling for shards
    async def on_shard_error(self, shard_id, error):
        logger.error(f"Shard {shard_id} encountered an error: {error}")

        if self.shard_monitor.monitoring_enabled:
            description = f"Shard {shard_id} encountered an error"
            fields = [
                {"name": "❌ Error Type", "value": type(error).__name__, "inline": True},
                {
                    "name": "📝 Error Details",
                    "value": f"```{str(error)[:500]}```",
                    "inline": False,
                },
            ]

            await self.shard_monitor.send_shard_embed(
                title="🚨 Shard Error",
                description=description,
                color=0xEF4444,
                shard_id=shard_id,
                fields=fields,
            )

    # Called when the bot joins a new guild
    async def on_guild_join(self, guild):
        logger.info(
            f"Joined new guild: {guild.name} (ID: {guild.id}) on shard {guild.shard_id}"
        )
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.add_server(guild)
            logger.info(f"Added {guild.name} to server tracker")

            # Send shard-specific guild join notification
            if self.shard_monitor.monitoring_enabled:
                shard_guilds = [g for g in self.guilds if g.shard_id == guild.shard_id]
                description = f"Joined **{guild.name}** on shard {guild.shard_id}"
                fields = [
                    {"name": "🏷️ Server ID", "value": str(guild.id), "inline": True},
                    {
                        "name": "👥 Members",
                        "value": str(guild.member_count),
                        "inline": True,
                    },
                    {
                        "name": "🔢 Shard ID",
                        "value": str(guild.shard_id),
                        "inline": True,
                    },
                    {
                        "name": "📈 Shard Guilds",
                        "value": str(len(shard_guilds)),
                        "inline": True,
                    },
                ]

                await self.shard_monitor.send_shard_embed(
                    title="📥 Joined Guild",
                    description=description,
                    color=0x3B82F6,
                    shard_id=guild.shard_id,
                    fields=fields,
                )
        except Exception as e:
            logger.error(f"Error adding guild to tracker: {e}")

    # Called when the bot is removed from a guild
    async def on_guild_remove(self, guild):
        logger.info(
            f"Removed from guild: {guild.name} (ID: {guild.id}) on shard {guild.shard_id}"
        )
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.remove_server(guild.id)
            logger.info(f"Removed {guild.name} from server tracker")

            # Send shard-specific guild leave notification
            if self.shard_monitor.monitoring_enabled:
                shard_guilds = [g for g in self.guilds if g.shard_id == guild.shard_id]
                description = f"Left **{guild.name}** on shard {guild.shard_id}"
                fields = [
                    {"name": "🏷️ Server ID", "value": str(guild.id), "inline": True},
                    {
                        "name": "👥 Members",
                        "value": str(guild.member_count),
                        "inline": True,
                    },
                    {
                        "name": "🔢 Shard ID",
                        "value": str(guild.shard_id),
                        "inline": True,
                    },
                    {
                        "name": "📉 Shard Guilds",
                        "value": str(len(shard_guilds)),
                        "inline": True,
                    },
                ]

                await self.shard_monitor.send_shard_embed(
                    title="📤 Left Guild",
                    description=description,
                    color=0xEF4444,
                    shard_id=guild.shard_id,
                    fields=fields,
                )
        except Exception as e:
            logger.error(f"Error removing guild from tracker: {e}")

    # Clean up resources when bot shuts down
    async def close(self):
        logger.info("Shutting down bot...")

        # Cancel hourly update task
        if self.hourly_update_task:
            self.hourly_update_task.cancel()
            try:
                await self.hourly_update_task
            except asyncio.CancelledError:
                logger.info("Hourly update task cancelled")

        # Close shard monitor session
        await self.shard_monitor.close()

        # Call parent close method
        await super().close()


async def main():
    bot = HEATLabsBot()

    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        # Send critical error to shard webhook if possible
        if bot.shard_monitor.monitoring_enabled:
            try:
                await bot.shard_monitor.send_shard_embed(
                    title="🚨 Critical Bot Error",
                    description="Bot failed to start",
                    color=0xEF4444,
                    shard_id=0,
                    fields=[
                        {
                            "name": "❌ Error Type",
                            "value": type(e).__name__,
                            "inline": True,
                        },
                        {
                            "name": "📝 Error Details",
                            "value": f"```{str(e)[:500]}```",
                            "inline": False,
                        },
                    ],
                )
            except:
                pass
    finally:
        # Clean up resources
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
