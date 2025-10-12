import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TeamCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/team.json"

    # Load team members from JSON file
    def load_team(self) -> list:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    logger.info("Team data loaded successfully")
                    return data.get("members", [])
            logger.warning(f"Team file not found: {self.config_file}")
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
