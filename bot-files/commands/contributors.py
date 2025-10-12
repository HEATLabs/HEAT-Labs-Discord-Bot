import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class ContributorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/contributors.json"

    # Load contributors from JSON file
    def load_contributor(self) -> list:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    logger.info("Contributors data loaded successfully")
                    return data.get("contributors", [])
            logger.warning(f"Contributors file not found: {self.config_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading contributors: {e}")
            return []

    @app_commands.command(
        name="contributors",
        description="View all HEAT Labs contributors",
    )
    async def contributors(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Contributors", color="#ff8300")
        logger.info(
            f"Contributors command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        members = self.load_contributor()

        if not members:
            embed.description = "⚠️ Failed to load contributors data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Contributors command failed: No members loaded for {interaction.user}"
            )
            return

        try:
            contributor_text = []
            for member in members:
                member_name = member.get("contributorName", "Unknown")
                member_description = member.get(
                    "contributorDescription", "No description specified"
                )
                contributor_text.append(f"• **{member_name}** - {member_description}")

            embed.description = "\n".join(contributor_text)
            await interaction.followup.send(embed=embed)
            logger.info(f"Contributors command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing contributors data for {interaction.user}: {e}")
            embed.description = "⚠️ Error processing contributors data. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ContributorCommands(bot))
    logger.info("ContributorCommands cog loaded")
