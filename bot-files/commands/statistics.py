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

    # Format creation date to remove time
    def format_creation_date(self, creation_date_str: str) -> str:
        try:
            # Parse the full date and reformat without time
            creation_date = datetime.strptime(creation_date_str, "%B %d, %Y %H:%M:%S")
            return creation_date.strftime("%B %d, %Y")
        except Exception as e:
            logger.error(f"Error formatting creation date: {e}")
            # Fallback
            return (
                creation_date_str.split(" ")[0]
                + " "
                + creation_date_str.split(" ")[1]
                + " "
                + creation_date_str.split(" ")[2]
            )

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

        stats_data = self.load_statistics()

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
            # Get and format data
            creation_date_raw = stats_data.get("creationDate", "Unknown")
            coffee_per_day = stats_data.get("coffeePerDay", 0)

            # Format creation date and calculate coffee
            if creation_date_raw != "Unknown":
                creation_date = self.format_creation_date(creation_date_raw)
                total_coffee = self.calculate_total_coffee(
                    creation_date_raw, coffee_per_day
                )
            else:
                creation_date = "Unknown"
                total_coffee = 0

            # Add creation date and coffee stats
            coffee_field_value = f"**Creation Date:** {creation_date}\n**Coffee Consumption:** around {coffee_per_day} cups per day"
            if total_coffee > 0:
                coffee_field_value += (
                    f"\n**Total Coffee Emptied:** {total_coffee:,} cups"
                )

            embed.add_field(
                name="📊 Project Overview", value=coffee_field_value, inline=False
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
                    inline=True,
                )

                # Project structure stats
                embed.add_field(
                    name="📁 Project Structure",
                    value=(
                        f"**Files:** {stats.get('filesCount', 0):,}\n"
                        f"**Folders:** {stats.get('foldersCount', 0):,}\n"
                        f"**Total Size:** {stats.get('totalSizeGB', 0)} GB"
                    ),
                    inline=True,
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
