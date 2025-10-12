import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()

# Nation choices for autocomplete
TANK_NATIONS = ["All", "USA", "Germany", "USSR", "UK", "China", "France"]


class TanksListCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.tanks_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/tanks.json"

    async def fetch_tanks(self):
        try:
            async with self.session.get(self.tanks_url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Tanks data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch tanks data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching tanks data: {e}")
            return None

    @app_commands.command(
        name="tanks",
        description="View all available tanks in HEAT Labs, filtered by nation",
    )
    @app_commands.describe(nation="Select a nation or 'All' to view all tanks")
    @app_commands.choices(
        nation=[app_commands.Choice(name=n, value=n) for n in TANK_NATIONS]
    )
    async def tanks(
        self, interaction: discord.Interaction, nation: app_commands.Choice[str] = None
    ) -> None:
        await interaction.response.defer(thinking=True)

        selected_nation = nation.value if nation else "All"
        embed = create_embed(command_name=f"Tanks - {selected_nation}", color="#ff8300")
        logger.info(
            f"Tanks command invoked by {interaction.user} for nation '{selected_nation}' in guild {interaction.guild.name}"
        )

        tanks_data = await self.fetch_tanks()

        if not tanks_data:
            embed.description = "⚠️ Failed to fetch tanks data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Tanks command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            tanks = (
                tanks_data
                if isinstance(tanks_data, list)
                else tanks_data.get("tanks", [])
            )

            if not tanks:
                embed.description = "No tanks available."
                await interaction.followup.send(embed=embed)
                return

            # Group tanks by nation
            tanks_by_nation = {}
            for tank in tanks:
                nation_name = tank.get("nation", "Unknown")
                if nation_name not in tanks_by_nation:
                    tanks_by_nation[nation_name] = []
                tanks_by_nation[nation_name].append(tank.get("name", "Unknown"))

            # Filter by selected nation
            if selected_nation == "All":
                # Add fields for each nation
                for nation_name in sorted(tanks_by_nation.keys()):
                    tank_names = sorted(tanks_by_nation[nation_name])
                    embed.add_field(
                        name=f"🌍 {nation_name}",
                        value="\n".join(f"• {name}" for name in tank_names),
                        inline=False,
                    )
                total_tanks = len(tanks)
            else:
                # Show only selected nation
                if selected_nation not in tanks_by_nation:
                    embed.description = f"No tanks found for {selected_nation}."
                    await interaction.followup.send(embed=embed)
                    return

                tank_names = sorted(tanks_by_nation[selected_nation])
                embed.add_field(
                    name=f"🌍 {selected_nation}",
                    value="\n".join(f"• {name}" for name in tank_names),
                    inline=False,
                )
                total_tanks = len(tank_names)

            embed.set_footer(
                text=f"Total Tanks: {total_tanks}",
                icon_url="https://raw.githubusercontent.com/HEATlabs/HEAT-Labs-Discord-Bot/main/assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Tanks command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing tanks data for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing tanks data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("TanksListCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TanksListCommands(bot))
    logger.info("TanksListCommands cog loaded")
