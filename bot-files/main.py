import discord
from discord.ext import commands
import os
import asyncio
import traceback
from dotenv import load_dotenv
from modules.logger import get_logger
from modules.cooldown import global_cooldown

# Load environment variables
load_dotenv()

# Get logger instance
logger = get_logger()


class HEATLabsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

        # Check global cooldown
        self.tree.interaction_check = global_cooldown.interaction_check
        logger.info("HEAT Labs Bot initialized")

    # Load all command modules
    async def setup_hook(self):
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

    async def on_ready(self):
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is serving {len(self.guilds)} guilds")

        # Sync servers with the servers.json file
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.sync_servers(self.guilds)
            logger.info("Server sync completed successfully")
        except Exception as e:
            logger.error(f"Error during server sync: {e}")
            # Send to monitor if available
            if hasattr(self, 'monitor'):
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
            if hasattr(self, 'monitor'):
                await self.monitor.on_status_rotation_error(e)

        # Notify monitor that bot is ready
        if hasattr(self, 'monitor'):
            await self.monitor.on_bot_ready()

    # Called when the bot joins a new guild
    async def on_guild_join(self, guild):
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.add_server(guild)
            logger.info(f"Added {guild.name} to server tracker")
        except Exception as e:
            logger.error(f"Error adding guild to tracker: {e}")

    # Called when the bot is removed from a guild
    async def on_guild_remove(self, guild):
        logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.remove_server(guild.id)
            logger.info(f"Removed {guild.name} from server tracker")
        except Exception as e:
            logger.error(f"Error removing guild from tracker: {e}")


async def main():
    bot = HEATLabsBot()

    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        logger.error(f"Error starting bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
