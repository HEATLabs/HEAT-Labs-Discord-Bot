import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class AgentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.agents_url = "https://cdn1.heatlabs.net/agents.json"

    async def fetch_agents(self):
        try:
            async with self.session.get(self.agents_url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Agents data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch agents data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching agents data: {e}")
            return None

    # Generate autocomplete choices for agent names
    def get_agent_choices(self, agents_data):
        if not agents_data:
            return []
        agents = agents_data.get("agents", [])
        return [
            app_commands.Choice(name=agent["name"], value=agent["name"])
            for agent in agents
        ]

    # Autocomplete callback for agent names
    async def agent_autocomplete(self, interaction: discord.Interaction, current: str):
        agents_data = await self.fetch_agents()
        if not agents_data:
            return []

        agents = agents_data.get("agents", [])
        choices = [agent["name"] for agent in agents]
        return [
            app_commands.Choice(name=choice, value=choice)
            for choice in choices
            if current.lower() in choice.lower()
        ]

    @app_commands.command(
        name="agent",
        description="View detailed information about a specific HEAT Labs agent",
    )
    @app_commands.describe(name="The name of the agent you want to view")
    @app_commands.autocomplete(name=agent_autocomplete)
    async def agent(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Agent command invoked by {interaction.user} for agent '{name}' in guild {interaction.guild.name}"
        )

        agents_data = await self.fetch_agents()

        if not agents_data:
            embed = create_embed(command_name="Agent", color="#ff8300")
            embed.description = (
                "⚠️ Failed to fetch agents data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Agent command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            agents = agents_data.get("agents", [])

            # Find the agent by name (case-insensitive)
            agent = next((a for a in agents if a["name"].lower() == name.lower()), None)

            if not agent:
                embed = create_embed(command_name="Agent", color="#ff8300")
                embed.description = f"❌ Agent '{name}' not found. Please check the spelling and try again."
                await interaction.followup.send(embed=embed)
                logger.warning(f"Agent '{name}' not found for {interaction.user}")
                return

            # Create the main embed
            embed = create_embed(
                command_name=f"Agent - {agent['name']}", color="#ff8300"
            )

            # Add agent image
            if agent.get("image"):
                embed.set_image(url=agent["image"])

            # Add specialty section
            specialty = agent.get("specialty", "Unknown")
            embed.add_field(name="🎯 Specialty", value=specialty, inline=False)

            # Add specialty description
            description = agent.get("description", "No description available.")
            embed.add_field(
                name="📝 Ability Description", value=description, inline=False
            )

            # Add story section
            story = agent.get("story", "No story available.")
            embed.add_field(name="📖 Story", value=story, inline=False)

            # Add compatible tanks section
            compatible_tanks = agent.get("compatibleTanks", [])
            if compatible_tanks:
                tank_names = "\n".join(f"• {tank['name']}" for tank in compatible_tanks)
                embed.add_field(
                    name="🛡️ Compatible Tanks", value=tank_names, inline=False
                )
            else:
                embed.add_field(
                    name="🛡️ Compatible Tanks",
                    value="No compatible tanks available.",
                    inline=False,
                )

            # Add status badge
            status = agent.get("status", "Unknown")
            status_emoji = "✅" if status == "Available Now" else "🔒"
            embed.add_field(
                name="Status", value=f"{status_emoji} {status}", inline=True
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Agent command completed successfully for {interaction.user} (Agent: {agent['name']})"
            )

        except Exception as e:
            logger.error(f"Error processing agent data for {interaction.user}: {e}")
            embed = create_embed(command_name="Agent", color="#ff8300")
            embed.description = (
                "⚠️ Error processing agent data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("AgentCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AgentCommands(bot))
    logger.info("AgentCommands cog loaded")
