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
                    "**`/tank(s) {name}`** – View all tanks or detailed stats of one.\n"
                    "**`/map(s) {name}`** – List all maps or view details and strategy of one.\n"
                    "**`/agent(s) {name}`** – List all agents or see one’s abilities and stats.\n"
                    "**`/tournament(s) {name}`** – View all tournaments or details of a specific one.\n"
                    "**`/player(s) {name}`** – List or check stats of players *[In Development]*.\n"
                    "**`/contact`** – Send feedback or reports to the HEAT Labs team.\n"
                    "**`/domains`** – Show all active HEAT Labs domains.\n"
                    "**`/socials`** – Get links to official HEAT Labs platforms.\n"
                    "**`/team`** – View current HEAT Labs team members and roles.\n"
                    "**`/contributors`** – Show all project contributors.\n"
                    "**`/playground`** – List all experimental features.\n"
                    "**`/debug`** – Developer-only for internal testing.\n"
                    "**`/status`** – Check the status of our systems.\n"
                    "**`/ping`** – Check bot latency."
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
