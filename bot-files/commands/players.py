import discord
from discord.ext import commands
from discord import app_commands
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class PlayersCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="players",
        description="View all players - Feature in development",
    )
    async def players(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Players", color="#ff8300")
        logger.info(
            f"Players command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        try:
            embed.description = "🔧 This feature is currently in development"
            embed.add_field(
                name="Coming Soon",
                value=(
                    "The `/players` command will return a complete list of all players "
                    "with their statistics and rankings. Our team is working hard to "
                    "bring you this functionality soon!"
                ),
                inline=False,
            )

            embed.add_field(
                name="What to Expect",
                value=(
                    "• Complete player listings\n"
                    "• Player statistics and rankings\n"
                    "• Search and filter capabilities\n"
                    "• Detailed player profiles"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Players command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing players command for {interaction.user}: {e}"
            )
            embed.description = "⚠️ Error processing command. Please try again later."
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlayersCommands(bot))
    logger.info("PlayersCommands cog loaded")
