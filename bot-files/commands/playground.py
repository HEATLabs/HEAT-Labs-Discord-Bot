import discord
from discord.ext import commands
from discord import app_commands
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class PlaygroundCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="playground",
        description="Explore all HEAT Labs playground features and experimental tools",
    )
    async def playground(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Playground", color="#ff8300")
        logger.info(
            f"Playground command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        try:
            # Main description
            embed.description = "Explore experimental features, tier lists, countdowns, and community tools built around World of Tanks: HEAT. Stay ahead with behind-the-scenes updates and exclusive developer content."

            # Available Features
            embed.add_field(
                name="🎮 Available Playground Features",
                value=(
                    "🎯 [**Tier List Creator**](https://heatlabs.net/playground/tierlist) - Create your own ranking for tanks, maps and agents\n"
                    "⚙️ [**Game Configurator**](https://heatlabs.net/playground/configurator) - Customize your World of Tanks: HEAT experience\n"
                    "🎲 [**Tank Roulette**](https://heatlabs.net/playground/roulette) - Spin the roulette to get a random tank to play\n"
                    "🖥️ [**Game Servers**](https://heatlabs.net/playground/game-servers) - Live tracking for all World of Tanks: HEAT game servers\n"
                    "📱 [**HEAT Labs Application**](https://heatlabs.net/playground/heat-labs-app) - Download our app on your Phone or Desktop\n"
                    "📝 [**Wordle Game**](https://heatlabs.net/playground/wordle) - World of Tanks: HEAT inspired Wordle game\n"
                    "🔊 [**Soundboard**](https://heatlabs.net/playground/soundboard) - Listen to all sounds from World of Tanks: HEAT\n"
                    "⏰ [**Alpha 3 Countdown**](https://heatlabs.net/playground/alpha-3-playtest) - Countdown for the launch of Alpha 3 playtest\n"
                ),
                inline=False,
            )

            # Quick Access
            embed.add_field(
                name="🔗 Quick Access",
                value=(
                    "• Visit our [Playground](https://heatlabs.net/playground) section for the full experience\n"
                    "• Join our [Discord](https://discord.heatlabs.net) for updates and community\n"
                    "• Check [Status](https://status.heatlabs.net) for system availability\n"
                ),
                inline=False,
            )

            # Tips
            embed.add_field(
                name="💡 Tips",
                value=(
                    "• These are experimental features - expect frequent updates!\n"
                    "• Found a bug? Use `/contact` to report it to our team\n"
                    "• Want to suggest a new feature? Join our Discord and share your ideas!"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Playground command completed successfully for {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error processing playground command for {interaction.user}: {e}"
            )
            embed.description = (
                "⚠️ Error loading playground features. Please try again later."
            )
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlaygroundCommands(bot))
    logger.info("PlaygroundCommands cog loaded")
