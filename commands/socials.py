import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from modules.embeds import create_embed


class SocialsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config/socials.json"

    # Load socials from JSON file
    def load_socials(self) -> list:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("socials", [])
            logging.error(f"Socials file not found: {self.config_file}")
            return []
        except Exception as e:
            logging.error(f"Error loading socials: {e}")
            return []

    @app_commands.command(
        name="socials",
        description="View all official HEAT Labs social media and community links",
    )
    async def socials(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Socials", color="#ff8300")

        socials = self.load_socials()

        if not socials:
            embed.description = (
                "⚠️ Failed to load socials data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            return

        try:
            for social in socials:
                social_name = social.get("socialName", "Unknown")
                social_description = social.get(
                    "socialDescription", "No description available"
                )
                social_url = social.get("socialURL", "")

                # Create clickable field value with the URL
                field_value = f"{social_description}\n[Visit →]({social_url})\n\n"

                embed.add_field(
                    name=social_name,
                    value=field_value,
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"Error processing socials: {e}")
            embed.description = (
                "⚠️ Error processing socials data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SocialsCommands(bot))
