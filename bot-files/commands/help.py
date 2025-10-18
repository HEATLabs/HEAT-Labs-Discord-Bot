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
                    "**`/tanks`** - Returns a list of all tanks.\n"
                    "**`/tank {tank-name}`** - Shows detailed stats and background for a specific tank.\n"
                    "**`/maps`** - Lists all available maps.\n"
                    "**`/map {map-name}`** - Displays layout, features, and strategic overview of a map.\n"
                    "**`/agents`** - Returns all agents.\n"
                    "**`/agent {agent-name}`** - Shows abilities, stats, and tactical insights of an agent.\n"
                    "**`/tournaments`** - Lists all tournaments.\n"
                    "**`/tournament {tournament-name}`** - Provides details including teams and results.\n"
                    "**`/players`** - Lists all players *[In Development]*.\n"
                    "**`/player {player-name}`** - Shows stats for a specific player *[In Development]*.\n"
                    "**`/contact`** - Send a one-way message to the HEAT Labs team for feedback or reports.\n"
                    "**`/domains`** - Displays all active HEAT Labs domains and their purposes.\n"
                    "**`/socials`** - Links to official HEAT Labs social platforms.\n"
                    "**`/team`** - Lists all current HEAT Labs team members and roles.\n"
                    "**`/contributors`** - Lists all project contributors.\n"
                    "**`/help`** - Displays this help menu."
                ),
                inline=False,
            )

            # Tips
            embed.add_field(
                name="💡 Tips",
                value=(
                    "• Use `/help` anytime to see this menu again.\n"
                    "• Command names are case-insensitive.\n"
                    "• For more information, visit the bot's [documentation](https://discord.heatlabs.net)."
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
