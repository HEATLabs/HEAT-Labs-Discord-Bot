import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class SocialsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/socials.json"

    # Load socials from JSON file
    def load_socials(self) -> list:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    logger.info("Socials data loaded successfully")
                    return data.get("socials", [])
            logger.warning(f"Socials file not found: {self.config_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading socials: {e}")
            return []

    @app_commands.command(
        name="socials",
        description="View all official HEAT Labs social media and community links",
    )
    async def socials(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Socials", color="#ff8300")
        logger.info(
            f"Socials command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        socials = self.load_socials()

        if not socials:
            embed.description = (
                "⚠️ Failed to load socials data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Socials command failed: No socials loaded for {interaction.user}"
            )
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
            logger.info(
                f"Socials command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(f"Error processing socials for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing socials data. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SocialsCommands(bot))
    logger.info("SocialsCommands cog loaded")
