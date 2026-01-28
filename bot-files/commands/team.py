import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/team.json"

    # Load team members from JSON file
    def load_team(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Team data loaded successfully")
                return data.get("members", [])
            else:
                logger.warning(
                    f"Failed to fetch team members: HTTP {response.status_code}"
                )
                return []
        except Exception as e:
            logger.error(f"Error loading team: {e}")
            return []

    @app_commands.command(
        name="team",
        description="View the HEAT Labs team members and their roles",
    )
    async def team(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Team", color="#ff8300")
        logger.info(
            f"Team command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        members = self.load_team()

        if not members:
            embed.description = "⚠️ Failed to load team data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Team command failed: No members loaded for {interaction.user}"
            )
            return

        try:
            team_text = []
            for member in members:
                member_name = member.get("memberName", "Unknown")
                member_description = member.get(
                    "memberDescription", "No role specified"
                )
                team_text.append(f"• **{member_name}** - {member_description}")

            embed.description = "\n".join(team_text)
            await interaction.followup.send(embed=embed)
            logger.info(f"Team command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing team data for {interaction.user}: {e}")
            embed.description = "⚠️ Error processing team data. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TeamCommands(bot))
    logger.info("TeamCommands cog loaded")
