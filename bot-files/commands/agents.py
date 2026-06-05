import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()

# Status choices for filtering
AGENT_STATUS = ["Available Now"]


class AgentsListCommands(commands.Cog):
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

    @app_commands.command(
        name="agents",
        description="View all available agents in HEAT Labs",
    )
    async def agents(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name=f"Agents - Available Now", color="#ff8300")
        logger.info(
            f"Agents command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        agents_data = await self.fetch_agents()

        if not agents_data:
            embed.description = (
                "⚠️ Failed to fetch agents data. Please try again later."
            )
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Agents command failed: Unable to fetch data for {interaction.user}"
            )
            return

        try:
            agents = agents_data.get("agents", [])

            # Filter to only agents
            available_agents = [agent for agent in agents if agent.get("status") == "Available Now"]

            if not available_agents:
                embed.description = "No available agents found."
                await interaction.followup.send(embed=embed)
                return

            # List all available agents
            agent_names = sorted([agent.get("name", "Unknown") for agent in available_agents])

            embed.add_field(
                name="✅ Available Agents",
                value="\n".join(f"• {name}" for name in agent_names),
                inline=False,
            )

            embed.add_field(
                name="📊 Total",
                value=f"{len(available_agents)} Agent{'s' if len(available_agents) != 1 else ''}",
                inline=True,
            )

            await interaction.followup.send(embed=embed)
            logger.info(f"Agents command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing agents data for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error processing agents data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("AgentsListCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AgentsListCommands(bot))
    logger.info("AgentsListCommands cog loaded")
