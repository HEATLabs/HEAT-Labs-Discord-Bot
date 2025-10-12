import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from modules.embeds import create_embed


class DomainsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/domains.json"

    # Load domains from JSON file
    def load_domains(self) -> list:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("domains", [])
            logging.error(f"Domains file not found: {self.config_file}")
            return []
        except Exception as e:
            logging.error(f"Error loading domains: {e}")
            return []

    @app_commands.command(
        name="domains",
        description="View all official HEAT Labs domains and services",
    )
    async def domains(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Domains", color="#ff8300")

        domains = self.load_domains()

        if not domains:
            embed.description = (
                "⚠️ Failed to load domains data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
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

        except Exception as e:
            logging.error(f"Error processing domains: {e}")
            embed.description = (
                "⚠️ Error processing domains data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DomainsCommands(bot))
