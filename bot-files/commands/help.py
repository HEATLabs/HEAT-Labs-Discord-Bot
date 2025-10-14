import discord
from discord.ext import commands
from discord import app_commands
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="View all available HEAT Labs bot commands",
    )
    async def help(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Help", color="#ff8300")
        logger.info(
            f"Help command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        try:
            # All Commands
            embed.add_field(
                name="📚 Available Commands",
                value=(
                    "**`/tanks`** - "
                    "Returns complete list of all tanks.\n"
                    "**`/tank {tank-name}`** - "
                    "Returns detailed information, stats, and background for the specified tank.\n"
                    "**`/maps`** - "
                    "Returns complete list of all maps.\n"
                    "**`/map {map-name}`** - "
                    "Displays map details including layout, features, and strategic overview.\n"
                    "**`/agents`** - "
                    "Returns complete list of all agents.\n"
                    "**`/agent {agent-name}`** - "
                    "Shows complete agent information such as abilities, stats, and tactical insights.\n"
                    "**`/tournaments`** - "
                    "Returns complete list of all tournaments.\n"
                    "**`/tournament {agent-name}`** - "
                    "Provides detailed information about a specific tournament, including teams and results.\n"
                    "**`/domains`** - "
                    "Shows a complete list of all active HEAT Labs domains and their respective purposes.\n"
                    "**`/socials`** - "
                    "Provides direct links to all official HEAT Labs social platforms and community pages.\n"
                    "**`/team`** - "
                    "Lists all current HEAT Labs team members along with their roles and contributions.\n"
                    "**`/contributors`** - "
                    "Lists all contributors who have helped improve the HEAT Labs project.\n"
                    "**`/help`** - "
                    "View this help menu with all available commands."
                ),
                inline=False,
            )

            # Tips
            embed.add_field(
                name="💡 Tips",
                value=(
                    "• Use `/help` anytime to see this menu again.\n"
                    "• Command names are case-insensitive.\n"
                    "• For more information, visit [HEAT Labs](https://heatlabs.net)"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Help command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing help command for {interaction.user}: {e}")
            embed.description = "⚠️ Error loading help menu. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommands(bot))
    logger.info("HelpCommands cog loaded")
