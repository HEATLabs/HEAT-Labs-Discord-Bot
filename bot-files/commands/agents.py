import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()

# Status choices for filtering
AGENT_STATUS = ["All", "Available", "Unreleased"]


class AgentsListCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.agents_url = ""https://cdn1.heatlabs.net/agents.json"

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
        description="View all available agents in HEAT Labs, filtered by status",
    )
    @app_commands.describe(status="Select agent status: All, Available, or Unreleased")
    @app_commands.choices(
        status=[app_commands.Choice(name=s, value=s) for s in AGENT_STATUS]
    )
    async def agents(
        self, interaction: discord.Interaction, status: app_commands.Choice[str] = None
    ) -> None:
        await interaction.response.defer(thinking=True)

        selected_status = status.value if status else "All"
        embed = create_embed(
            command_name=f"Agents - {selected_status}", color="#ff8300"
        )
        logger.info(
            f"Agents command invoked by {interaction.user} for status '{selected_status}' in guild {interaction.guild.name}"
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

            if not agents:
                embed.description = "No agents available."
                await interaction.followup.send(embed=embed)
                return

            # Separate agents by status
            available_agents = []
            unreleased_agents = []

            for agent in agents:
                name = agent.get("name", "Unknown")
                agent_status = agent.get("status", "Unknown")

                if agent_status == "Available Now":
                    available_agents.append(name)
                else:
                    unreleased_agents.append((name, agent_status))

            # Filter by selected status
            total_agents = 0
            if selected_status == "All":
                # Show both available and unreleased
                if available_agents:
                    embed.add_field(
                        name="✅ Available Agents",
                        value="\n".join(
                            f"• {name}" for name in sorted(available_agents)
                        ),
                        inline=False,
                    )

                if unreleased_agents:
                    embed.add_field(
                        name="🔒 Unreleased Agents",
                        value="\n".join(
                            f"• {name} ({status})"
                            for name, status in sorted(
                                unreleased_agents, key=lambda x: x[0]
                            )
                        ),
                        inline=False,
                    )
                total_agents = len(available_agents) + len(unreleased_agents)

            elif selected_status == "Available":
                # Show only available agents
                if available_agents:
                    embed.add_field(
                        name="✅ Available Agents",
                        value="\n".join(
                            f"• {name}" for name in sorted(available_agents)
                        ),
                        inline=False,
                    )
                    total_agents = len(available_agents)
                else:
                    embed.description = "No available agents found."
                    await interaction.followup.send(embed=embed)
                    return

            elif selected_status == "Unreleased":
                # Show only unreleased agents
                if unreleased_agents:
                    embed.add_field(
                        name="🔒 Unreleased Agents",
                        value="\n".join(
                            f"• {name} ({status})"
                            for name, status in sorted(
                                unreleased_agents, key=lambda x: x[0]
                            )
                        ),
                        inline=False,
                    )
                    total_agents = len(unreleased_agents)
                else:
                    embed.description = "No unreleased agents found."
                    await interaction.followup.send(embed=embed)
                    return

            embed.add_field(
                name="📊 Total",
                value=f"{total_agents} Agent{'s' if total_agents != 1 else ''}",
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
