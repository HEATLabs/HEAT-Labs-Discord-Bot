import discord
from discord.ext import commands
from discord import app_commands
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class ContactCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="contact",
        description="Contact the HEAT Labs team for support, feedback, or to join our team",
    )
    async def contact(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Contact", color="#ff8300")
        logger.info(
            f"Contact command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        try:
            # Contact description
            embed.description = (
                "Get in touch with the HEAT Labs team through the following forms:"
            )

            # Contact options
            embed.add_field(
                name="📝 Submit Community Guides",
                value=(
                    "Have you created a guide for the HEAT Labs community? "
                    "Share your knowledge and help other players!\n"
                    "[**Submit Your Guide →**](https://docs.google.com/forms/d/e/1FAIpQLScWeYSWgbenem3kpz9AiPiS3r3x8GkAhQAydsh6gl623e7gtA/viewform?usp=dialog)"
                ),
                inline=False,
            )

            embed.add_field(
                name="🗺️ Map Contributions & Guides",
                value=(
                    "Want to contribute to our map database? "
                    "Submit your map analyses, strategies, or guide content.\n"
                    "[**Contribute to Maps →**](https://docs.google.com/forms/d/e/1FAIpQLSfsqX6RmXbbCp1DBCOciOaXQNL3vNGLlKfMd_UZT_40nIkahg/viewform?usp=dialog)"
                ),
                inline=False,
            )

            embed.add_field(
                name="💡 Website Feedback & Ideas",
                value=(
                    "Found a bug? Have suggestions for improvement? "
                    "We'd love to hear your feedback!\n"
                    "[**Share Feedback →**](https://docs.google.com/forms/d/e/1FAIpQLScT8h8Ox9sQsg07O6kEhq9LNMARkRd5e6iR2287GgahlHNvAQ/viewform?usp=dialog)"
                ),
                inline=False,
            )

            embed.add_field(
                name="👥 Join Our Team",
                value=(
                    "Interested in joining the HEAT Labs team? "
                    "We're always looking for passionate contributors and new team members!\n"
                    "[**Apply to Join →**](https://docs.google.com/forms/d/e/1FAIpQLSfXyWU2eMX4Pd0xKa4NIUIFEEb2asJ4UtyxoJvlVArrh3RDfA/viewform?usp=dialog)"
                ),
                inline=False,
            )

            # Additional information
            embed.add_field(
                name="💬 Need Immediate Help?",
                value=(
                    "For urgent matters or direct communication, "
                    "you can also reach out to our team members directly on Discord.\n"
                    "[**Join our Discord server →**](https://discord.com/invite/caEFCA9ScF)"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Contact command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing contact command for {interaction.user}: {e}"
            )
            embed.description = (
                "⚠️ Error loading contact information. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ContactCommands(bot))
    logger.info("ContactCommands cog loaded")
