import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


# Manages daily log files for the HEAT Labs Bot
class DailyLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self._ensure_log_dir_exists()
        self.logger = self._setup_logger()

    # Create logs directory if it doesn't exist
    def _ensure_log_dir_exists(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    # Generate log filename based on current date
    def _get_log_filename(self) -> str:
        return os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    # Set up logger with console and file handlers
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("HEATLabsBot")
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to prevent duplicates
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

        # File handler with daily rotation
        log_filename = self._get_log_filename()
        file_handler = RotatingFileHandler(
            log_filename,
            mode="a",
            maxBytes=10485760,  # 10MB
            backupCount=0,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

        return logger

    # Get the configured logger instance
    def get_logger(self) -> logging.Logger:
        return self.logger

    # Log when a command is executed
    def log_command_executed(self, command_name: str, user: str, guild: str):
        self.logger.info(
            f"Command executed: '{command_name}' by {user} in guild '{guild}'"
        )

    # Log command errors
    def log_command_error(self, command_name: str, user: str, error: str):
        self.logger.error(f"Command error: '{command_name}' by {user} - {error}")

    # Log data fetching operations
    def log_data_fetch(self, source: str, success: bool, details: str = ""):
        status = "SUCCESS" if success else "FAILED"
        message = f"Data fetch [{status}] from {source}"
        if details:
            message += f" - {details}"
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, message)

    # Log guild join/leave events
    def log_guild_event(self, event_type: str, guild_name: str, guild_id: int):
        self.logger.info(f"Guild {event_type}: {guild_name} (ID: {guild_id})")

    # Log cache operations
    def log_cache_operation(self, operation: str, status: str, details: str = ""):
        message = f"Cache {operation}: {status}"
        if details:
            message += f" - {details}"
        level = logging.INFO if status == "SUCCESS" else logging.WARNING
        self.logger.log(level, message)

    # Log server synchronization
    def log_server_sync(self, added: int, removed: int):
        self.logger.info(f"Server sync completed: {added} added, {removed} removed")


# Initialize the daily logger
daily_logger = DailyLogger()
get_logger = daily_logger.get_logger
