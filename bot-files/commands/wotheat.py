import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class WotHeatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/wotheat.json"

    # Load WoT HEAT pages from JSON file
    def load_wotheat_pages(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("WoT: HEAT pages data loaded successfully")
                return data.get("wotheat", [])
            else:
                logger.warning(
                    f"Failed to fetch WoT: HEAT pages: HTTP {response.status_code}"
                )
                return []
        except Exception as e:
            logger.error(f"Error loading WoT: HEAT pages: {e}")
            return []

    @app_commands.command(
        name="wotheat",
        description="View all official World of Tanks: HEAT store pages and social media",
    )
    async def wotheat(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="World of Tanks: HEAT", color="#ff8300")
        logger.info(
            f"WoT: HEAT command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        wotheat_pages = self.load_wotheat_pages()

        if not wotheat_pages:
            embed.description = "⚠️ Failed to load World of Tanks: HEAT pages data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"WoT: HEAT command failed: No pages loaded for {interaction.user}"
            )
            return

        try:
            for page in wotheat_pages:
                page_name = page.get("pageName", "Unknown")
                page_description = page.get(
                    "pageDescription", "No description available"
                )
                page_url = page.get("pageURL", "")

                # Create clickable field value with the URL
                field_value = f"{page_description}\n[Visit →]({page_url})\n\n"

                embed.add_field(
                    name=page_name,
                    value=field_value,
                    inline=False,
                )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"WoT: HEAT command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing WoT: HEAT pages for {interaction.user}: {e}"
            )
            embed.description = "⚠️ Error processing World of Tanks: HEAT pages data. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WotHeatCommands(bot))
    logger.info("WotHeatCommands cog loaded")
