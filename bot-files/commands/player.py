import discord
from discord.ext import commands
from discord import app_commands
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="player",
        description="Get detailed information about a specific player - Feature in development",
    )
    @app_commands.describe(player_name="Name of the player to look up")
    async def player(self, interaction: discord.Interaction, player_name: str) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Player", color="#ff8300")
        logger.info(
            f"Player command invoked by {interaction.user} for player '{player_name}' in guild {interaction.guild.name}"
        )

        try:
            embed.description = "🔧 This feature is currently in development"
            embed.add_field(
                name="Coming Soon",
                value=(
                    f"The `/player` command for **{player_name}** will provide detailed "
                    "player information including statistics, match history, and performance "
                    "metrics. Our team is working hard to bring you this functionality soon!"
                ),
                inline=False,
            )

            embed.add_field(
                name="What to Expect",
                value=(
                    "• Detailed player profile\n"
                    "• Performance statistics\n"
                    "• Match history\n"
                    "• Ranking information\n"
                    "• Achievement tracking"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Player command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing player command for {interaction.user}: {e}")
            embed.description = "⚠️ Error processing command. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlayerCommands(bot))
    logger.info("PlayerCommands cog loaded")
