import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class SupporterCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/supporters.json"

    # Load supporters from JSON file
    def load_supporter(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Supporter data loaded successfully")
                return data.get("supporters", [])
            else:
                logger.warning(f"Failed to fetch supporters: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading supporters: {e}")
            return []

    @app_commands.command(
        name="supporters",
        description="View all HEAT Labs supporters",
    )
    async def supporters(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Supporters", color="#ff8300")
        logger.info(
            f"Supporters command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        members = self.load_supporter()

        if not members:
            embed.description = "⚠️ Failed to load supporters data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Supporters command failed: No members loaded for {interaction.user}"
            )
            return

        try:
            supporter_text = []
            for member in members:
                member_name = member.get("supporterName", "Unknown")
                member_description = member.get(
                    "supporterDescription", "No description specified"
                )
                supporter_text.append(f"• **{member_name}** - {member_description}")

            embed.description = "\n".join(supporter_text)
            await interaction.followup.send(embed=embed)
            logger.info(f"Supporters command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing supporters data for {interaction.user}: {e}")
            embed.description = "⚠️ Error processing supporters data. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SupporterCommands(bot))
    logger.info("SupporterCommands cog loaded")
