import discord
import asyncio
import json
import os
from modules.logger import get_logger

logger = get_logger()


class StatusRotator:
    def __init__(self, bot):
        self.bot = bot
        self.rotation_task = None
        self.is_rotating = False
        self.config_dir = "config"
        self.status_file = os.path.join(self.config_dir, "status.json")

        # Load statuses from JSON file
        self.statuses = self._load_statuses()

        if self.statuses:
            logger.info(
                f"Status rotator initialized with {len(self.statuses)} status variations"
            )
        else:
            logger.warning("No statuses loaded, status rotation will not start")

    # Load statuses from JSON file
    def _load_statuses(self) -> list:
        try:
            if not os.path.exists(self.status_file):
                logger.error(f"Status file not found: {self.status_file}")
                return []

            with open(self.status_file, "r") as f:
                data = json.load(f)
                statuses = data.get("statuses", [])

                if not statuses:
                    logger.warning("No statuses found in status.json file")

                return statuses

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing status.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading status file: {e}")
            return []

    # Get rotation interval from JSON file
    def _get_rotation_interval(self) -> int:
        try:
            if not os.path.exists(self.status_file):
                return 20

            with open(self.status_file, "r") as f:
                data = json.load(f)
                return data.get("rotation_interval", 20)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading rotation interval: {e}")
            return 20

    # Convert string to discord activity type
    def _get_activity_type(self, type_str: str) -> discord.ActivityType:
        type_map = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing,
        }
        return type_map.get(type_str.lower(), discord.ActivityType.playing)

    # Rotate statuses at the specified interval
    async def start_rotation(self, interval: int = None):
        if self.is_rotating:
            logger.warning("Status rotation is already running")
            return

        # Check if we have statuses to rotate
        if not self.statuses:
            logger.error("Cannot start status rotation - no statuses available")
            return

        # Use interval from config if not specified
        if interval is None:
            interval = self._get_rotation_interval()

        self.is_rotating = True
        self.rotation_task = asyncio.create_task(self._rotation_loop(interval))
        logger.info(f"Status rotation started with {interval} second interval")

    # Stop the status rotation
    async def stop_rotation(self):
        if self.rotation_task:
            self.rotation_task.cancel()
            self.is_rotating = False
            logger.info("Status rotation stopped")

    # Main rotation loop
    async def _rotation_loop(self, interval: int):
        current_index = 0

        while self.is_rotating:
            try:
                # Reload statuses from file in case they were updated
                self.statuses = self._load_statuses()

                if not self.statuses:
                    logger.warning("No statuses available, stopping rotation")
                    self.is_rotating = False
                    break

                # Get current status
                status = self.statuses[current_index]

                # Process dynamic placeholders
                status_name = self._process_placeholders(status["name"])

                # Get activity type
                activity_type = self._get_activity_type(status["type"])

                # Update bot status
                activity = discord.Activity(type=activity_type, name=status_name)

                await self.bot.change_presence(activity=activity)
                logger.debug(f"Status updated: {status.get('message', status_name)}")

                # Move to next status
                current_index = (current_index + 1) % len(self.statuses)

                # Wait for the specified interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Status rotation task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in status rotation: {e}")
                # Continue rotation even if one status fails
                await asyncio.sleep(interval)

    # Process dynamic placeholders in status text
    def _process_placeholders(self, text: str) -> str:
        processed = text

        # Replace server count placeholder
        if "{server_count}" in processed:
            processed = processed.replace("{server_count}", str(len(self.bot.guilds)))

        # Replace user count placeholder
        if "{user_count}" in processed:
            total_users = sum(guild.member_count for guild in self.bot.guilds)
            processed = processed.replace("{user_count}", str(total_users))

        return processed

    # Reload statuses from JSON file
    def reload_statuses(self):
        self.statuses = self._load_statuses()
        if self.statuses:
            logger.info(f"Reloaded {len(self.statuses)} statuses from file")
        else:
            logger.warning("No statuses found when reloading")
        return len(self.statuses)

    # Get the number of statuses in rotation
    def get_status_count(self) -> int:
        return len(self.statuses)

    # Get a list of all current statuses
    def get_current_statuses(self) -> list:
        return self.statuses.copy()
