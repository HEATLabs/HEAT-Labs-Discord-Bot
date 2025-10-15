import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class TankCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.tanks_url = "https://cdn1.heatlabs.net/tanks.json"

    # Fetch JSON data from URL
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

    # Autocomplete callback for tank names
    async def tank_autocomplete(self, interaction: discord.Interaction, current: str):
        tanks_data = await self.fetch_data(self.tanks_url)
        if not tanks_data:
            return []

        tanks = (
            tanks_data if isinstance(tanks_data, list) else tanks_data.get("tanks", [])
        )
        choices = [tank["name"] for tank in tanks]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ][
            :25
        ]  # Discord limit

    @app_commands.command(
        name="tank",
        description="View detailed information about a specific HEAT Labs tank",
    )
    @app_commands.describe(name="The name of the tank you want to view")
    @app_commands.autocomplete(name=tank_autocomplete)
    async def tank(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Tank command invoked by {interaction.user} for tank '{name}' in guild {interaction.guild.name}"
        )

        # Fetch all required data
        tanks_data = await self.fetch_data(self.tanks_url)

        if not tanks_data:
            embed = create_embed(command_name="Tank", color="#ff8300")
            embed.description = "⚠️ Failed to fetch tank data. Please try again later."
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Tank command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            tanks = (
                tanks_data
                if isinstance(tanks_data, list)
                else tanks_data.get("tanks", [])
            )

            # Find the tank by name (case-insensitive)
            tank = next((t for t in tanks if t["name"].lower() == name.lower()), None)

            if not tank:
                embed = create_embed(command_name="Tank", color="#ff8300")
                embed.description = f"❌ Tank '{name}' not found. Please check the spelling and try again."
                await interaction.followup.send(embed=embed)
                logger.warning(f"Tank '{name}' not found for {interaction.user}")
                return

            # Fetch tank-specific abilities and agents
            abilities_data = None
            agents_data = None

            if tank.get("abilities"):
                abilities_data = await self.fetch_data(tank["abilities"])

            if tank.get("agents"):
                agents_data = await self.fetch_data(tank["agents"])

            # Create the main embed
            embed = create_embed(command_name=f"Tank - {tank['name']}", color="#ff8300")

            # Add tank image
            if tank.get("image"):
                embed.set_image(url=tank["image"])

            # Add basic info
            nation = tank.get("nation", "Unknown")
            tank_type = tank.get("type", "Unknown")
            tank_class = tank.get("class", "Unknown")

            embed.add_field(name="🌍 Nation", value=nation, inline=True)

            embed.add_field(name="🎯 Type", value=tank_type, inline=True)

            embed.add_field(name="📊 Class", value=tank_class, inline=True)

            # Find and add compatible agents
            if agents_data:
                agent_list = agents_data.get("agents", [])

                if agent_list:
                    for agent in agent_list:
                        agent_name = agent.get("name", "Unknown")
                        specialty = agent.get("specialty", "Unknown")
                        description = agent.get(
                            "description", "No description available."
                        )

                        embed.add_field(
                            name=f"👤 Agent - {agent_name}",
                            value=f"**Specialty:** {specialty}\n**Description:** {description}",
                            inline=False,
                        )

                        # Add agent image if available
                        if agent.get("image"):
                            embed.set_thumbnail(url=agent["image"])

            # Find and add tank abilities
            if abilities_data:
                primary_attack = abilities_data.get("primaryAttack", [])
                tank_abilities = abilities_data.get("tankAbilities", [])

                # Add primary attack
                if primary_attack:
                    for attack in primary_attack:
                        attack_name = attack.get("name", "Unknown")
                        attack_desc = attack.get(
                            "description", "No description available."
                        )
                        embed.add_field(
                            name=f"🔫 Primary Attack - {attack_name}",
                            value=attack_desc,
                            inline=False,
                        )

                # Add tank abilities (skip agent ability since its already shown)
                if tank_abilities:
                    for ability in tank_abilities:
                        ability_name = ability.get("name", "Unknown")
                        ability_desc = ability.get(
                            "description", "No description available."
                        )
                        embed.add_field(
                            name=f"⚡ Ability - {ability_name}",
                            value=ability_desc,
                            inline=False,
                        )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Tank command completed successfully for {interaction.user} (Tank: {tank['name']})"
            )

        except Exception as e:
            logger.error(f"Error processing tank data for {interaction.user}: {e}")
            embed = create_embed(command_name="Tank", color="#ff8300")
            embed.description = "⚠️ Error processing tank data. Please try again later."
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("TankCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TankCommands(bot))
    logger.info("TankCommands cog loaded")
