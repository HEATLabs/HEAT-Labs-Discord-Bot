import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from datetime import datetime
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TournamentsListCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.tournaments_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/tournaments.json"

    async def fetch_tournaments(self):
        try:
            async with self.session.get(self.tournaments_url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Tournaments data fetched successfully")
                    return data
                logger.warning(
                    f"Failed to fetch tournaments data: HTTP {response.status}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching tournaments data: {e}")
            return None

    # Format date string to a more readable format (22 Feb. 2025)
    def format_date(self, date_string: str) -> str:
        try:
            # Try parsing as ISO format first
            if "T" in date_string:
                dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(date_string)

            # Format as "22 Feb. 2025"
            return dt.strftime("%d %b. %Y")
        except (ValueError, AttributeError):
            return date_string  # Return original if parsing fails

    # Format datetime string to a more readable format (22 Feb. 2025 14:00 UTC)
    def format_datetime(self, datetime_string: str) -> str:
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))

            # Format as "22 Feb. 2025 14:00 UTC"
            return dt.strftime("%d %b. %Y %H:%M UTC")
        except (ValueError, AttributeError):
            return datetime_string  # Return original if parsing fails

    @app_commands.command(
        name="tournaments",
        description="View all available tournaments in HEAT Labs",
    )
    async def tournaments(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Tournaments", color="#ff8300")
        logger.info(
            f"Tournaments command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        tournaments_data = await self.fetch_tournaments()

        if not tournaments_data:
            embed.description = (
                "⚠️ Failed to fetch tournaments data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Tournaments command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            if not tournaments_data:
                embed.description = "No tournaments available."
                await interaction.followup.send(embed=embed)
                return

            for tournament in tournaments_data:
                if not tournament.get("publish"):
                    continue

                name = tournament.get("name", "Unknown")
                description = tournament.get("description", "No description available.")
                start = self.format_datetime(tournament.get("start", "Unknown"))
                end = self.format_datetime(tournament.get("end", "Unknown"))
                mode = tournament.get("mode", "Unknown")
                tournament_type = tournament.get("type", "Unknown")
                date = self.format_date(tournament.get("date", "Unknown"))

                tournament_info = (
                    f"**Description:** {description}\n"
                    f"**Date:** {date}\n"
                    f"**Start:** {start}\n"
                    f"**End:** {end}\n"
                    f"**Mode:** {mode}\n"
                    f"**Status:** {tournament_type}"
                )

                embed.add_field(
                    name=f"🏆 {name}",
                    value=tournament_info,
                    inline=False,
                )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Tournaments command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing tournaments data for {interaction.user}: {e}"
            )
            embed.description = (
                "⚠️ Error processing tournaments data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("TournamentsListCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TournamentsListCommands(bot))
    logger.info("TournamentsListCommands cog loaded")
