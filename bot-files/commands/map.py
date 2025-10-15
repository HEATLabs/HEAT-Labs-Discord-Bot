import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class MapCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.maps_url = ""https://cdn1.heatlabs.net/maps.json"

    async def fetch_maps(self):
        try:
            async with self.session.get(self.maps_url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Maps data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch maps data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching maps data: {e}")
            return None

    # Autocomplete callback for map names
    async def map_autocomplete(self, interaction: discord.Interaction, current: str):
        maps_data = await self.fetch_maps()
        if not maps_data:
            return []

        maps = maps_data.get("maps", [])
        choices = [m["name"] for m in maps]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ][
            :25
        ]  # Discord limit

    @app_commands.command(
        name="map",
        description="View detailed information about a specific HEAT Labs map",
    )
    @app_commands.describe(name="The name of the map you want to view")
    @app_commands.autocomplete(name=map_autocomplete)
    async def map(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Map command invoked by {interaction.user} for map '{name}' in guild {interaction.guild.name}"
        )

        maps_data = await self.fetch_maps()

        if not maps_data:
            embed = create_embed(command_name="Map", color="#ff8300")
            embed.description = "⚠️ Failed to fetch maps data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Map command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            maps = maps_data.get("maps", [])

            # Find the map by name (case-insensitive)
            map_data = next(
                (m for m in maps if m["name"].lower() == name.lower()), None
            )

            if not map_data:
                embed = create_embed(command_name="Map", color="#ff8300")
                embed.description = f"❌ Map '{name}' not found. Please check the spelling and try again."
                await interaction.followup.send(embed=embed)
                logger.warning(f"Map '{name}' not found for {interaction.user}")
                return

            # Create the main embed
            embed = create_embed(
                command_name=f"Map - {map_data['name']}", color="#ff8300"
            )

            # Add map image
            if map_data.get("image"):
                embed.set_image(url=map_data["image"])

            # Add description
            description = map_data.get("description", "No description available.")
            embed.add_field(name="📝 Description", value=description, inline=False)

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Map command completed successfully for {interaction.user} (Map: {map_data['name']})"
            )

        except Exception as e:
            logger.error(f"Error processing map data for {interaction.user}: {e}")
            embed = create_embed(command_name="Map", color="#ff8300")
            embed.description = "⚠️ Error processing map data. Please try again later."
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("MapCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MapCommands(bot))
    logger.info("MapCommands cog loaded")
