import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class DomainsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/domains.json"

    # Load domains from JSON file
    def load_domains(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Domains data loaded successfully")
                return data.get("domains", [])
            else:
                logger.warning(f"Failed to fetch domains: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error loading domains: {e}")
            return []

    @app_commands.command(
        name="domains",
        description="View all official HEAT Labs domains and services",
    )
    async def domains(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Domains", color="#ff8300")
        logger.info(
            f"Domains command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        domains = self.load_domains()

        if not domains:
            embed.description = (
                "⚠️ Failed to load domains data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Domains command failed: No domains loaded for {interaction.user}"
            )
            return

        try:
            for domain in domains:
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
                f"Domains command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error processing domains for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing domains data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DomainsCommands(bot))
    logger.info("DomainsCommands cog loaded")
