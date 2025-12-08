import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import random
from modules.embeds import create_embed, add_embed_footer
from modules.logger import get_logger

logger = get_logger()


class RandomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

        # JSON data URLs
        self.tanks_url = "https://cdn1.heatlabs.net/tanks.json"
        self.maps_url = "https://cdn1.heatlabs.net/maps.json"
        self.agents_url = "https://cdn1.heatlabs.net/agents.json"

    # Fetch data from URL
    async def fetch_data(self, url: str):
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    return data
                logger.warning(
                    f"Failed to fetch data from {url}: HTTP {response.status}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    # Filter items by state
    def filter_by_state(self, items):
        if isinstance(items, dict) and "agents" in items:
            # Handle agents.json structure
            items_list = items.get("agents", [])
        elif isinstance(items, dict) and "maps" in items:
            # Handle maps.json structure
            items_list = items.get("maps", [])
        elif isinstance(items, list):
            # Handle tanks.json structure
            items_list = items
        else:
            items_list = []

        # Filter only items with state "displayed"
        return [item for item in items_list if item.get("state") == "displayed"]

    # Get a random item from filtered list
    def get_random_item(self, items_list):
        if not items_list:
            return None
        return random.choice(items_list)

    # Create tank embed
    def create_tank_embed(self, tank):
        tank_name = tank.get("name", "Unknown Tank")
        tank_slug = tank.get("slug", "")
        tank_nation = tank.get("nation", "Unknown Nation")
        tank_type = tank.get("type", "Unknown Type")
        tank_class = tank.get("class", "Unknown Class")
        tank_image = tank.get("image", "")

        embed = create_embed(
            command_name="Random Tank",
            description=f"🎲 **Your Random Tank Selection** 🎲\n\n**{tank_name}** has been randomly chosen for you!",
            color="#ff8300",
        )

        # Add tank image if available
        if tank_image:
            embed.set_image(url=tank_image)

        embed.add_field(name="🌍 Nation", value=tank_nation, inline=True)

        embed.add_field(name="🎯 Type", value=tank_type, inline=True)

        embed.add_field(name="📊 Class", value=tank_class, inline=True)

        # Add link to tank details
        if tank_slug:
            embed.add_field(
                name="🔗 View Details",
                value=f"[Click here to learn more about the {tank_name}](https://heatlabs.net/tanks/{tank_slug})",
                inline=False,
            )

        return embed

    # Create map embed
    def create_map_embed(self, map_item):
        map_name = map_item.get("name", "Unknown Map")
        map_slug = map_item.get("slug", "")
        map_description = map_item.get("description", "No description available.")
        map_image = map_item.get("image", "")

        embed = create_embed(
            command_name="Random Map",
            description=f"🗺️ **Your Random Map Selection** 🗺️\n\n**{map_name}** has been randomly chosen for you!",
            color="#ff8300",
        )

        # Add map image if available
        if map_image:
            embed.set_image(url=map_image)

        embed.add_field(name="📍 Description", value=map_description, inline=False)

        # Add link to map details
        if map_slug:
            embed.add_field(
                name="🔗 View Details",
                value=f"[Click here to learn more about {map_name}](https://heatlabs.net/maps/{map_slug})",
                inline=False,
            )

        return embed

    # Create agent embed
    def create_agent_embed(self, agent):
        agent_name = agent.get("name", "Unknown Agent")
        agent_slug = agent.get("slug", "")
        agent_specialty = agent.get("specialty", "Unknown Specialty")
        agent_status = agent.get("status", "Unknown Status")
        agent_story = agent.get("story", "No story available.")
        agent_image = agent.get("image", "")

        embed = create_embed(
            command_name="Random Agent",
            description=f"👤 **Your Random Agent Selection** 👤\n\n**{agent_name}** has been randomly chosen for you!",
            color="#ff8300",
        )

        # Add agent image if available
        if agent_image:
            embed.set_thumbnail(url=agent_image)

        embed.add_field(name="⚡ Specialty", value=agent_specialty, inline=True)

        embed.add_field(name="📈 Status", value=agent_status, inline=True)

        # Truncate story if too long
        if len(agent_story) > 200:
            agent_story = agent_story[:197] + "..."

        embed.add_field(name="📝 Story", value=agent_story, inline=False)

        # Add link to agent details
        if agent_slug:
            embed.add_field(
                name="🔗 View Details",
                value=f"[Click here to learn more about {agent_name}](https://heatlabs.net/agents/{agent_slug})",
                inline=False,
            )

        return embed

    @app_commands.command(
        name="random", description="Get a random tank, map, or agent suggestion"
    )
    @app_commands.describe(type="What would you like to get a random selection of?")
    @app_commands.choices(
        type=[
            app_commands.Choice(name="tank", value="tank"),
            app_commands.Choice(name="map", value="map"),
            app_commands.Choice(name="agent", value="agent"),
        ]
    )
    async def random_command(
        self, interaction: discord.Interaction, type: app_commands.Choice[str]
    ) -> None:
        await interaction.response.defer(thinking=True)

        selection_type = type.value
        logger.info(
            f"Random command invoked by {interaction.user} for type '{selection_type}' in guild {interaction.guild.name}"
        )

        # Fetch data based on selection type
        if selection_type == "tank":
            data = await self.fetch_data(self.tanks_url)
            type_name = "tank"
            type_display = "Tank"
        elif selection_type == "map":
            data = await self.fetch_data(self.maps_url)
            type_name = "map"
            type_display = "Map"
        elif selection_type == "agent":
            data = await self.fetch_data(self.agents_url)
            type_name = "agent"
            type_display = "Agent"
        else:
            # Should not happen due to choices validation
            embed = create_embed(
                command_name="Random",
                description="❌ Invalid selection type. Please choose tank, map, or agent.",
                color="#ff8300",
            )
            await interaction.followup.send(embed=embed)
            return

        if not data:
            embed = create_embed(
                command_name=f"Random {type_display}",
                description=f"❌ Could not fetch {type_name} data. Please try again later.",
                color="#ff8300",
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Random command failed: Unable to fetch {type_name} data for {interaction.user}"
            )
            return

        # Filter and get random item
        filtered_items = self.filter_by_state(data)
        random_item = self.get_random_item(filtered_items)

        if not random_item:
            embed = create_embed(
                command_name=f"Random {type_display}",
                description=f"❌ No {type_name}s available for random selection.",
                color="#ff8300",
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Random command failed: No {type_name}s available for {interaction.user}"
            )
            return

        # Create appropriate embed based on type
        if selection_type == "tank":
            embed = self.create_tank_embed(random_item)
        elif selection_type == "map":
            embed = self.create_map_embed(random_item)
        elif selection_type == "agent":
            embed = self.create_agent_embed(random_item)

        # Add a fun footer note
        embed.add_field(
            name="💡 Try Again?",
            value=f"Run `/random` again to get a different random {type_name}!",
            inline=False,
        )

        await interaction.followup.send(embed=embed)
        logger.info(
            f"Random {type_name} command completed successfully for {interaction.user}"
        )

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("RandomCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RandomCommands(bot))
    logger.info("RandomCommands cog loaded")
