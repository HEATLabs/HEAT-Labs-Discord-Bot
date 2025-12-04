import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from datetime import datetime
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TournamentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.tournaments_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/tournaments.json"

    async def fetch_data(self, url: str):
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    return data
                logger.warning(
                    f"Failed to fetch data from {url}: HTTP {response.status}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
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

    # Autocomplete callback for tank names
    async def tournament_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        tournaments_data = await self.fetch_data(self.tournaments_url)
        if not tournaments_data:
            return []

        choices = [t["name"] for t in tournaments_data if t.get("publish")]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ][:25]

    @app_commands.command(
        name="tournament",
        description="View detailed information about a specific HEAT Labs tournament",
    )
    @app_commands.describe(name="The name of the tournament you want to view")
    @app_commands.autocomplete(name=tournament_autocomplete)
    async def tournament(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Tournament command invoked by {interaction.user} for tournament '{name}' in guild {interaction.guild.name}"
        )

        tournaments_data = await self.fetch_data(self.tournaments_url)

        if not tournaments_data:
            embed = create_embed(command_name="Tournament", color="#ff8300")
            embed.description = (
                "⚠️ Failed to fetch tournament data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Tournament command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            tournament = next(
                (t for t in tournaments_data if t["name"].lower() == name.lower()), None
            )

            if not tournament:
                embed = create_embed(command_name="Tournament", color="#ff8300")
                embed.description = f"❌ Tournament '{name}' not found. Please check the spelling and try again."
                await interaction.followup.send(embed=embed)
                logger.warning(f"Tournament '{name}' not found for {interaction.user}")
                return

            tournament_data = await self.fetch_data(tournament["tournament-data"])

            if not tournament_data:
                embed = create_embed(command_name="Tournament", color="#ff8300")
                embed.description = (
                    "⚠️ Failed to fetch tournament details. Please try again later."
                )
                await interaction.followup.send(embed=embed)
                logger.warning(
                    f"Tournament details not found for {name} ({interaction.user})"
                )
                return

            embed = create_embed(
                command_name=f"Tournament - {tournament['name']}", color="#ff8300"
            )

            if tournament.get("image"):
                embed.set_image(url=tournament["image"])

            embed.add_field(
                name="📝 Description",
                value=tournament.get("description", "No description available."),
                inline=False,
            )

            # Use formatted dates
            formatted_date = self.format_date(tournament.get("date", "Unknown"))
            formatted_start = self.format_datetime(tournament.get("start", "Unknown"))
            formatted_end = self.format_datetime(tournament.get("end", "Unknown"))

            embed.add_field(name="📅 Date", value=formatted_date, inline=True)
            embed.add_field(name="🕐 Start", value=formatted_start, inline=True)
            embed.add_field(name="🕔 End", value=formatted_end, inline=True)
            embed.add_field(
                name="🎮 Mode", value=tournament.get("mode", "Unknown"), inline=True
            )
            embed.add_field(
                name="📊 Status", value=tournament.get("type", "Unknown"), inline=True
            )

            total_teams = tournament_data.get("total_teams", "Unknown")
            embed.add_field(
                name="👥 Total Teams",
                value=total_teams,
                inline=True,
            )

            top_3_teams = tournament_data.get("top_3_teams", [])

            if top_3_teams:
                embed.add_field(name="🏆 Top Teams", value="", inline=False)

                for idx, team in enumerate(top_3_teams, 1):
                    team_name = team.get("team_name", "Unknown")
                    team_captain = team.get("team_captain", "Unknown")
                    team_members = team.get("team_members", "")

                    tank_info = []
                    team_tanks = team.get("team_tanks", [])
                    for member in team_tanks:
                        tank_name = member.get("tank_name", "Unknown")
                        tank_info.append(tank_name)

                    tanks_list = (
                        ", ".join(tank_info) if tank_info else "No tanks available."
                    )

                    medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉"
                    team_info = (
                        f"**Captain:** {team_captain}\n"
                        f"**Members:** {team_members}\n"
                        f"**Tanks:** {tanks_list}"
                    )

                    embed.add_field(
                        name=f"{medal} #{idx} - {team_name}",
                        value=team_info,
                        inline=False,
                    )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Tournament command completed successfully for {interaction.user} (Tournament: {tournament['name']})"
            )

        except Exception as e:
            logger.error(
                f"Error processing tournament data for {interaction.user}: {e}"
            )
            embed = create_embed(command_name="Tournament", color="#ff8300")
            embed.description = (
                "⚠️ Error processing tournament data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("TournamentCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TournamentCommands(bot))
    logger.info("TournamentCommands cog loaded")
