import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class PartnersCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/partners.json"

    # Load partners from JSON file
    def load_partners(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Partners data loaded successfully")
                return data.get("partners", [])
            else:
                logger.warning(f"Failed to fetch partners: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading partners: {e}")
            return []

    @app_commands.command(
        name="partners",
        description="Check out exclusive offers and perks from HEAT Labs partners.",
    )
    async def partners(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Partners", color="#ff8300")
        logger.info(
            f"Partners command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        partners = self.load_partners()

        if not partners:
            embed.description = (
                "⚠️ Failed to load partners data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Partners command failed: No partners loaded for {interaction.user}"
            )
            return

        try:
            for domain in partners:
                page_name = domain.get("pageName", "Unknown")
                page_description = domain.get(
                    "pageDescription", "No description available"
                )
                page_url = domain.get("pageURL", "")

                # Create clickable field value with the URL
                field_value = f"{page_description}\n[Visit →]({page_url})\n\n"

                embed.add_field(
                    name=page_name,
                    value=field_value,
                    inline=False,
                )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Partners command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error processing partners for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing partners data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PartnersCommands(bot))
    logger.info("PartnersCommands cog loaded")
