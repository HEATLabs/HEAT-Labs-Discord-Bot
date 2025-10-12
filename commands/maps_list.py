import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class MapsListCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.maps_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/maps.json"

    async def fetch_maps(self):
        try:
            async with self.session.get(self.maps_url) as response:
                if response.status == 200:
                    text = await response.text()
                    import json

                    data = json.loads(text)
                    logger.info("Maps data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch maps data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching maps data: {e}")
            return None

    @app_commands.command(
        name="maps",
        description="View all available maps in HEAT Labs",
    )
    async def maps(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Maps", color="#ff8300")
        logger.info(
            f"Maps command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        maps_data = await self.fetch_maps()

        if not maps_data:
            embed.description = "⚠️ Failed to fetch maps data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Maps command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            maps = maps_data.get("maps", [])

            if not maps:
                embed.description = "No maps available."
                await interaction.followup.send(embed=embed)
                return

            # Create map list
            map_names = sorted([m.get("name", "Unknown") for m in maps])

            # Add all maps in one column
            embed.add_field(
                name="🗺️ Maps",
                value="\n".join(f"• {name}" for name in map_names),
                inline=False,
            )

            embed.set_footer(
                text=f"Total Maps: {len(maps)}",
                icon_url="https://raw.githubusercontent.com/HEATlabs/HEAT-Labs-Discord-Bot/main/assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Maps command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing maps data for {interaction.user}: {e}")
            embed.description = "⚠️ Error processing maps data. Please try again later."
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("MapsListCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MapsListCommands(bot))
    logger.info("MapsListCommands cog loaded")
