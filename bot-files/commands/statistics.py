import discord
from discord.ext import commands
from discord import app_commands
import json
import requests
from datetime import datetime
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class StatisticsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/home-stats.json"
        self.changelog_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/changelog.json"
        self.game_builds_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/game_builds.json"

    # Load statistics from JSON file
    def load_statistics(self) -> dict:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Statistics data loaded successfully")
                return data
            else:
                logger.warning(
                    f"Failed to fetch statistics: HTTP {response.status_code}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            return {}

    # Load changelog data
    def load_changelog(self) -> dict:
        try:
            response = requests.get(self.changelog_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Changelog data loaded successfully")
                return data
            else:
                logger.warning(
                    f"Failed to fetch changelog: HTTP {response.status_code}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error loading changelog: {e}")
            return {}

    # Load game builds data
    def load_game_builds(self) -> dict:
        try:
            response = requests.get(self.game_builds_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Game builds data loaded successfully")
                return data
            else:
                logger.warning(
                    f"Failed to fetch game builds: HTTP {response.status_code}"
                )
                return {}
        except Exception as e:
            logger.error(f"Error loading game builds: {e}")
            return {}

    # Calculate total coffee cups since creation date
    def calculate_total_coffee(
        self, creation_date_str: str, coffee_per_day: int
    ) -> int:
        try:
            # Parse the creation date
            creation_date = datetime.strptime(creation_date_str, "%B %d, %Y %H:%M:%S")
            current_date = datetime.now()

            # Calculate days difference
            days_since_creation = (current_date - creation_date).days
            total_coffee = days_since_creation * coffee_per_day

            return max(total_coffee, 0)
        except Exception as e:
            logger.error(f"Error calculating total coffee: {e}")
            # Fallback
            return 0

    # Calculate days since creation
    def calculate_days_since_creation(self, creation_date_str: str) -> int:
        try:
            # Parse the creation date
            creation_date = datetime.strptime(creation_date_str, "%B %d, %Y %H:%M:%S")
            current_date = datetime.now()

            # Calculate days difference
            days_since_creation = (current_date - creation_date).days
            return max(days_since_creation, 0)
        except Exception as e:
            logger.error(f"Error calculating days since creation: {e}")
            # Fallback
            return 0

    # Format creation date to remove time
    def format_creation_date(self, creation_date_str: str) -> str:
        try:
            # Parse the full date and reformat without time
            creation_date = datetime.strptime(creation_date_str, "%B %d, %Y %H:%M:%S")
            return creation_date.strftime("%B %d, %Y")
        except Exception as e:
            logger.error(f"Error formatting creation date: {e}")
            # Fallback
            parts = creation_date_str.split(" ")
            if len(parts) >= 3:
                return f"{parts[0]} {parts[1]} {parts[2]}"
            return creation_date_str

    # Format date string to Month Day, Year format
    def format_date_nicely(self, date_str: str) -> str:
        try:
            # Try different date formats
            formats_to_try = [
                "%Y-%m-%d",
                "%B %d, %Y",
                "%Y.%m.%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
            ]

            for fmt in formats_to_try:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime("%B %d, %Y")
                except ValueError:
                    continue

            # If no format works, try to extract the date part
            if "T" in date_str:
                date_part = date_str.split("T")[0]
                try:
                    date_obj = datetime.strptime(date_part, "%Y-%m-%d")
                    return date_obj.strftime("%B %d, %Y")
                except ValueError:
                    pass

            return date_str
        except Exception as e:
            logger.error(f"Error formatting date '{date_str}': {e}")
            return date_str

    # Get latest changelog entry
    def get_latest_changelog_entry(self, changelog_data: dict) -> dict:
        if not changelog_data or "updates" not in changelog_data:
            return {}

        updates = changelog_data.get("updates", [])
        if not updates:
            return {}

        # Sort by date
        sorted_updates = sorted(updates, key=lambda x: x.get("date", ""), reverse=True)
        return sorted_updates[0] if sorted_updates else {}

    # Get latest game build
    def get_latest_game_build(self, game_builds_data: dict) -> dict:
        if not game_builds_data or "builds" not in game_builds_data:
            return {}

        builds = game_builds_data.get("builds", {})
        if not builds:
            return {}

        # There's only one game in the builds
        game_name = list(builds.keys())[0]
        game_builds = builds.get(game_name, {})

        if not game_builds:
            return {}

        # Find the build with the latest build_date
        latest_build_hash = None
        latest_build_date = None

        for build_hash, build_data in game_builds.items():
            build_info = build_data.get("build_info", {})
            build_date = build_info.get("build_date", "")

            if build_date:
                try:
                    # Parse the build date
                    build_date_obj = datetime.strptime(build_date, "%Y.%m.%d %H:%M:%S")
                    if latest_build_date is None or build_date_obj > latest_build_date:
                        latest_build_date = build_date_obj
                        latest_build_hash = build_hash
                except Exception:
                    continue

        if latest_build_hash:
            return game_builds.get(latest_build_hash, {}).get("build_info", {})

        return {}

    @app_commands.command(
        name="statistics",
        description="View HEAT Labs statistics and metrics",
    )
    async def statistics(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Statistics", color="#ff8300")
        logger.info(
            f"Statistics command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        # Load all data sources
        stats_data = self.load_statistics()
        changelog_data = self.load_changelog()
        game_builds_data = self.load_game_builds()

        if not stats_data:
            embed.description = (
                "⚠️ Failed to load statistics data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Statistics command failed: No data loaded for {interaction.user}"
            )
            return

        try:
            # Get and format main statistics data
            creation_date_raw = stats_data.get("creationDate", "Unknown")
            coffee_per_day = stats_data.get("coffeePerDay", 0)

            # Format creation date and calculate coffee
            if creation_date_raw != "Unknown":
                creation_date = self.format_creation_date(creation_date_raw)
                total_coffee = self.calculate_total_coffee(
                    creation_date_raw, coffee_per_day
                )
                days_since_creation = self.calculate_days_since_creation(
                    creation_date_raw
                )
            else:
                creation_date = "Unknown"
                total_coffee = 0
                days_since_creation = 0

            # Get latest changelog entry
            latest_update = self.get_latest_changelog_entry(changelog_data)
            latest_version = latest_update.get("version", "Unknown")
            latest_update_date = latest_update.get("date", "Unknown")

            # Format the update date nicely
            if latest_update_date != "Unknown":
                formatted_update_date = self.format_date_nicely(latest_update_date)
            else:
                formatted_update_date = "Unknown"

            # Get latest game build
            latest_game_build = self.get_latest_game_build(game_builds_data)
            game_version = latest_game_build.get("version_name", "Unknown")
            game_build_date = latest_game_build.get("build_date", "Unknown")
            compressed_size = latest_game_build.get("compressed_size", "Unknown")
            uncompressed_size = latest_game_build.get("uncompressed_size", "Unknown")

            # Format game build date nicely
            if game_build_date != "Unknown":
                formatted_game_build_date = self.format_date_nicely(game_build_date)
            else:
                formatted_game_build_date = "Unknown"

            # Add Project Overview section
            coffee_field_value = f"**Creation Date:** {creation_date}\n**Days Since Creation:** {days_since_creation:,} days\n**Coffee Consumption:** {coffee_per_day} cups per day"
            if total_coffee > 0:
                coffee_field_value += (
                    f"\n**Total Coffee Emptied:** {total_coffee:,} cups"
                )

            embed.add_field(
                name="📊 Project Overview", value=coffee_field_value, inline=False
            )

            # Add Website Version section
            website_info = f"**Website Version:** {latest_version}\n**Website Build:** {formatted_update_date}"
            embed.add_field(
                name="🌐 Website Information", value=website_info, inline=False
            )

            # Add Game Overview section
            if game_version != "Unknown":
                game_info = f"**Game Version:** {game_version}\n**Game Build:** {formatted_game_build_date}\n**Download Size:** {compressed_size}\n**Install Size:** {uncompressed_size}"
                embed.add_field(name="🎮 Game Overview", value=game_info, inline=False)
            else:
                embed.add_field(
                    name="🎮 Game Overview",
                    value="*No game build data available*",
                    inline=False,
                )

            # Add statistics fields
            stats = stats_data.get("stats", {})

            if stats:
                # Team and development stats
                embed.add_field(
                    name="👥 Team & Development",
                    value=(
                        f"**Team Members:** {stats.get('teamMembers', 0)}\n"
                        f"**Contributors:** {stats.get('contributors', 0)}\n"
                        f"**Lines of Code:** {stats.get('linesOfCode', 0):,}"
                    ),
                    inline=False,
                )

                # Project structure stats
                embed.add_field(
                    name="📁 Project Structure",
                    value=(
                        f"**Files:** {stats.get('filesCount', 0):,}\n"
                        f"**Folders:** {stats.get('foldersCount', 0):,}\n"
                        f"**Total Size:** {stats.get('totalSizeGB', 0)} GB"
                    ),
                    inline=False,
                )

                # Website analytics stats
                embed.add_field(
                    name="📈 Website Analytics",
                    value=(
                        f"**Data Served:** {stats.get('dataServed', 0)} GB\n"
                        f"**Data Cached:** {stats.get('dataCached', 0)} GB\n"
                        f"**Total Requests:** {stats.get('totalRequests', 0):,}\n"
                        f"**Total Visitors:** {stats.get('totalVisitors', 0):,}"
                    ),
                    inline=False,
                )

            # Add a fun fact or additional information
            total_files_folders = stats.get("filesCount", 0) + stats.get(
                "foldersCount", 0
            )
            files_count = stats.get("filesCount", 1)
            lines_per_file = (
                stats.get("linesOfCode", 0) / files_count if files_count > 0 else 0
            )

            embed.add_field(
                name="💡 Did You Know?",
                value=(
                    f"With {stats.get('filesCount', 0):,} files and {stats.get('foldersCount', 0):,} folders, "
                    f"that's {total_files_folders:,} total items in the project! "
                    f"Each file averages {lines_per_file:.1f} lines of code."
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Statistics command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error processing statistics for {interaction.user}: {e}")
            logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
            embed.description = (
                "⚠️ Error processing statistics data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatisticsCommands(bot))
    logger.info("StatisticsCommands cog loaded")
