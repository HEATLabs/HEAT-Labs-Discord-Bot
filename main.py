import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class HEATLabsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

    # Load all command modules
    async def setup_hook(self):
        loaded = []
        for filename in os.listdir("./commands"):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"commands.{filename[:-3]}"
                try:
                    await self.load_extension(module_name)
                    loaded.append(module_name)
                    logging.info(f"Successfully loaded: {module_name}")
                except Exception as e:
                    logging.error(f"Failed to load {module_name}: {e}")

        await self.tree.sync()
        logging.info("Commands synced with Discord")

    async def on_ready(self):
        logging.info(f"{self.user} has connected to Discord!")
        logging.info(f"Bot is ready and serving {len(self.guilds)} guilds")

        # Sync servers with the servers.json file
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.sync_servers(self.guilds)
            logging.info("Server sync completed successfully")
        except Exception as e:
            logging.error(f"Error during server sync: {e}")

        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="HEAT Labs"
        )
        await self.change_presence(activity=activity)

    # Called when the bot joins a new guild
    async def on_guild_join(self, guild):
        logging.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.add_server(guild)
            logging.info(f"Added {guild.name} to server tracker")
        except Exception as e:
            logging.error(f"Error adding guild to tracker: {e}")

    # Called when the bot is removed from a guild
    async def on_guild_remove(self, guild):
        logging.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
        try:
            from modules.servers import ServerTracker

            tracker = ServerTracker()
            tracker.remove_server(guild.id)
            logging.info(f"Removed {guild.name} from server tracker")
        except Exception as e:
            logging.error(f"Error removing guild from tracker: {e}")


async def main():
    bot = HEATLabsBot()

    try:
        await bot.start(os.getenv("DISCORD_TOKEN"))
    except Exception as e:
        logging.error(f"Error starting bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
