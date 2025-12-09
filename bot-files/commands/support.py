import discord
from discord.ext import commands
from discord import app_commands
import json
import requests
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class SupportCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/support.json"

    # Load support methods from JSON file
    def load_support_methods(self) -> list:
        try:
            response = requests.get(self.config_file)
            if response.status_code == 200:
                data = response.json()
                logger.info("Support methods data loaded successfully")
                return data.get("support", [])
            else:
                logger.warning(
                    f"Failed to fetch support methods: HTTP {response.status_code}"
                )
                return []
        except Exception as e:
            logger.error(f"Error loading support methods: {e}")
            return []

    @app_commands.command(
        name="support",
        description="Support HEAT Labs development and help sustain our services",
    )
    async def support(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Support", color="#ff8300")
        logger.info(
            f"Support command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        support_methods = self.load_support_methods()

        if not support_methods:
            embed.description = (
                "⚠️ Failed to load support methods. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Support command failed: No support methods loaded for {interaction.user}"
            )
            return

        try:
            # Main description
            embed.description = "Help sustain HEAT Labs. Every contribution directly supports our hosting, backend systems, and future tools for the community."

            # Support methods section
            embed.add_field(
                name="🤝 Ways to Support",
                value=(
                    "Your support helps us maintain servers, develop new features, "
                    "and provide free tools for the World of Tanks: HEAT community. "
                    "Every contribution makes a difference!"
                ),
                inline=False,
            )

            # List all support methods from JSON
            for method in support_methods:
                page_name = method.get("pageName", "Unknown Platform")
                page_description = method.get(
                    "pageDescription", "No description available"
                )
                page_url = method.get("pageURL", "https://heatlabs.net")

                # Create clickable field value with the URL
                field_value = (
                    f"{page_description}\n[Support via {page_name} →]({page_url})\n\n"
                )

                embed.add_field(
                    name=f"💖 {page_name}",
                    value=field_value,
                    inline=False,
                )

            # Additional information
            embed.add_field(
                name="💡 What Your Support Enables",
                value=(
                    "• **Server hosting** for all our tools and services\n"
                    "• **Development** of new features and improvements\n"
                    "• **API access** for real-time game data\n"
                    "• **Community events** and tournaments\n"
                    "• **Free tools** for all World of Tanks: HEAT players"
                ),
                inline=False,
            )

            embed.add_field(
                name="🙏 Thank You",
                value=(
                    "Whether you contribute financially or simply use our tools, "
                    "thank you for being part of the HEAT Labs community! "
                    "Every bit of support helps us continue our work."
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Support command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing support command for {interaction.user}: {e}"
            )
            embed.description = (
                "⚠️ Error loading support methods. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SupportCommands(bot))
    logger.info("SupportCommands cog loaded")
