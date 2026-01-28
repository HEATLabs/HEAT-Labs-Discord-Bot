import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TesterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/testers.json"

    # Load testers from JSON file
    def load_tester(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Tester data loaded successfully")
                return data.get("testers", [])
            else:
                logger.warning(f"Failed to fetch testers: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading testers: {e}")
            return []

    @app_commands.command(
        name="testers",
        description="View all HEAT Labs testers",
    )
    async def testers(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Testers", color="#ff8300")
        logger.info(
            f"Testers command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        members = self.load_tester()

        if not members:
            embed.description = (
                "⚠️ Failed to load testers data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Testers command failed: No members loaded for {interaction.user}"
            )
            return

        try:
            tester_text = []
            for member in members:
                member_name = member.get("testerName", "Unknown")
                member_description = member.get(
                    "testerDescription", "No description specified"
                )
                tester_text.append(f"• **{member_name}** - {member_description}")

            embed.description = "\n".join(tester_text)
            await interaction.followup.send(embed=embed)
            logger.info(
                f"Testers command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error processing testers data for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing testers data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TesterCommands(bot))
    logger.info("TesterCommands cog loaded")
