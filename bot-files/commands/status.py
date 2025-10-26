import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from datetime import datetime
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

        # API URLs
        self.status_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/system-status.json"
        self.uptime_robot_url = "https://api.uptimerobot.com/v2/getMonitors"
        self.uptime_robot_api_key = "ur2540855-8a25d33f16ec589715c9ab65"

        # Status mapping
        self.status_map = {
            "operational": {"emoji": "🟢", "name": "Operational"},
            "degraded": {"emoji": "🟡", "name": "Degraded Performance"},
            "partial_outage": {"emoji": "🟠", "name": "Partial Outage"},
            "major_outage": {"emoji": "🔴", "name": "Major Outage"},
            "maintenance": {"emoji": "🔧", "name": "Under Maintenance"},
        }

    # Fetch system status data from GitHub
    async def fetch_status_data(self):
        try:
            async with self.session.get(self.status_url) as response:
                if response.status == 200:
                    # Read the text content and parse as JSON
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Status data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch status data: HTTP {response.status}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from status data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching status data: {e}")
            return None

    # Fetch uptime and response time data from Uptime Robot
    async def fetch_uptime_data(self):
        try:
            form_data = aiohttp.FormData()
            form_data.add_field("api_key", self.uptime_robot_api_key)
            form_data.add_field("format", "json")
            form_data.add_field("logs", "1")
            form_data.add_field("response_times", "1")
            form_data.add_field("custom_uptime_ratios", "1-7-30")
            form_data.add_field("response_times_limit", "24")

            async with self.session.post(
                self.uptime_robot_url, data=form_data
            ) as response:
                if response.status == 200:
                    # Read text and parse JSON manually for Uptime Robot
                    text = await response.text()
                    data = json.loads(text)
                    if data.get("stat") == "ok":
                        logger.info("Uptime data fetched successfully")
                        return data
                    else:
                        logger.warning(
                            f"Uptime API error: {data.get('error', {}).get('message', 'Unknown error')}"
                        )
                        return None
                logger.warning(f"Failed to fetch uptime data: HTTP {response.status}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from uptime data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching uptime data: {e}")
            return None

    # Format uptime percentage with color indicators
    def format_uptime(self, uptime_ratio):
        if not uptime_ratio or uptime_ratio == "" or uptime_ratio == "0":
            return "N/A"

        try:
            uptime_percent = float(uptime_ratio)
            if uptime_percent >= 99.5:
                return f"🟢 {uptime_percent:.2f}%"
            elif uptime_percent >= 95.0:
                return f"🟡 {uptime_percent:.2f}%"
            else:
                return f"🔴 {uptime_percent:.2f}%"
        except (ValueError, TypeError):
            return "N/A"

    # Format response time with color indicators
    def format_response_time(self, response_time):
        if not response_time:
            return "N/A"

        try:
            response_time = int(response_time)
            if response_time < 100:
                return f"🟢 {response_time}ms"
            elif response_time < 500:
                return f"🟡 {response_time}ms"
            else:
                return f"🔴 {response_time}ms"
        except (ValueError, TypeError):
            return "N/A"

    # Determine overall system status based on individual systems
    def get_overall_status(self, systems):
        status_priority = {
            "major_outage": 4,
            "partial_outage": 3,
            "degraded": 2,
            "maintenance": 1,
            "operational": 0,
        }

        highest_status = "operational"
        maintenance_count = 0

        for system in systems:
            system_status = system.get("status", "operational")
            if system_status == "maintenance":
                maintenance_count += 1
            if status_priority.get(system_status, 0) > status_priority.get(
                highest_status, 0
            ):
                highest_status = system_status

        # If all systems are in maintenance, show maintenance status
        if maintenance_count == len(systems):
            return "maintenance"

        return highest_status

    # Create the main status embed
    def create_status_embed(self, status_data, uptime_data):
        systems = status_data.get("systems", [])
        overall_status = self.get_overall_status(systems)
        status_info = self.status_map.get(
            overall_status, self.status_map["operational"]
        )

        # Set color based on overall status
        if overall_status == "operational":
            color = "#22c55e"
        elif overall_status in ["degraded", "maintenance"]:
            color = "#eab308"
        else:
            color = "#ef4444"

        embed = create_embed(command_name="System Status", color=color)

        # Overall status
        last_updated = status_data.get("last_updated", datetime.now().isoformat())
        try:
            # Try to parse the timestamp
            if "Z" in last_updated:
                last_updated = last_updated.replace("Z", "+00:00")
            dt = datetime.fromisoformat(last_updated)
            timestamp = int(dt.timestamp())
        except (ValueError, TypeError):
            # Fallback to current time
            timestamp = int(datetime.now().timestamp())

        embed.add_field(
            name=f"{status_info['emoji']} Overall Status",
            value=f"**{status_info['name']}**\n*Last updated: <t:{timestamp}:R>*",
            inline=False,
        )

        return embed, overall_status

    # Add individual system status to the embed
    def add_systems_to_embed(self, embed, status_data):
        systems = status_data.get("systems", [])

        systems_field = ""
        for system in systems:
            system_name = system.get("name", "Unknown System")
            system_status = system.get("status", "operational")
            status_info = self.status_map.get(
                system_status, self.status_map["operational"]
            )

            # System status only with colored circle
            systems_field += f"{status_info['emoji']} **{system_name}** "

        # Add systems field to embed only if we have systems
        if systems_field:
            embed.add_field(name="📊 System Status", value=systems_field, inline=False)

    # Add server monitoring data from Uptime Robot
    def add_server_monitoring_to_embed(self, embed, uptime_data):
        if not uptime_data or "monitors" not in uptime_data:
            embed.add_field(
                name="📈 Server Monitoring",
                value="*Unable to fetch server monitoring data*",
                inline=False,
            )
            return

        monitors = uptime_data["monitors"]

        # Create fields for server monitoring
        server_field = ""
        uptime_24h_field = ""
        uptime_7d_field = ""

        for monitor in monitors:
            friendly_name = monitor.get("friendly_name", "Unknown Server")

            # Server name
            server_field += f"**{friendly_name}**\n"

            # Uptime data
            ratios = monitor.get("custom_uptime_ratio", "").split("-")
            uptime_24h = self.format_uptime(ratios[0] if len(ratios) >= 1 else None)
            uptime_7d = self.format_uptime(ratios[1] if len(ratios) >= 2 else None)

            # Response time
            response_time = self.format_response_time(
                monitor.get("average_response_time")
            )

            uptime_24h_field += f"{uptime_24h}\n"
            uptime_7d_field += f"{uptime_7d}\n"

        # Add server monitoring section
        if server_field:
            embed.add_field(name="🖥️ Server", value=server_field, inline=True)
            embed.add_field(name="🕒 Uptime (24h)", value=uptime_24h_field, inline=True)
            embed.add_field(name="📅 Uptime (7d)", value=uptime_7d_field, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)

    # Add recent incidents to the embed if any exist
    def add_incidents_to_embed(self, embed, status_data):
        incidents = status_data.get("incidents", [])
        if incidents:
            incidents_text = ""
            for incident in incidents[:3]:
                title = incident.get("title", "Unknown Incident")
                status = incident.get("status", "started")
                start_time = incident.get("start_time", "")

                status_text = self.format_incident_status(status)
                incidents_text += f"**{title}** - {status_text}\n"

                if start_time:
                    try:
                        if "Z" in start_time:
                            start_time = start_time.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(start_time)
                        timestamp = int(dt.timestamp())
                        incidents_text += f"*Started: <t:{timestamp}:R>*\n"
                    except (ValueError, TypeError):
                        incidents_text += f"*Started: {start_time}*\n"

                incidents_text += "\n"

            embed.add_field(
                name="🚨 Recent Incidents", value=incidents_text, inline=False
            )

    # Format incident status for display
    def format_incident_status(self, status):
        status_map = {
            "started": "🟡 Started",
            "identified": "🟠 Identified",
            "monitoring": "🔵 Monitoring",
            "in_progress": "🟣 In Progress",
            "ended": "🟢 Resolved",
        }
        return status_map.get(status, status)

    @app_commands.command(
        name="status",
        description="Check the current status of HEAT Labs systems and services",
    )
    async def status(self, interaction: discord.Interaction) -> None:
        # Send initial fetching message
        initial_embed = create_embed(command_name="System Status", color="#ff8300")
        initial_embed.description = "⏳ Fetching complete status data...\n*This may take a moment as we gather real-time metrics.*"

        await interaction.response.defer(thinking=True)
        message = await interaction.followup.send(embed=initial_embed)

        logger.info(
            f"Status command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        try:
            # Fetch data from both APIs
            status_data = await self.fetch_status_data()
            uptime_data = await self.fetch_uptime_data()

            if not status_data:
                error_embed = create_embed(
                    command_name="System Status", color="#ef4444"
                )
                error_embed.description = (
                    "❌ Failed to fetch status data. Please try again later."
                )
                await message.edit(embed=error_embed)
                logger.warning(
                    f"Status command failed: Unable to fetch data for {interaction.user}"
                )
                return

            # Create main embed with actual data
            embed, overall_status = self.create_status_embed(status_data, uptime_data)

            # Add system status
            self.add_systems_to_embed(embed, status_data)

            # Add server monitoring data from Uptime Robot
            self.add_server_monitoring_to_embed(embed, uptime_data)

            # Add incidents if any
            self.add_incidents_to_embed(embed, status_data)

            # Add helpful footer note
            embed.add_field(
                name="💡 Note",
                value="For detailed status information visit our [status page](https://status.heatlabs.net).",
                inline=False,
            )

            # Edit the original message with the complete embed
            await message.edit(embed=embed)
            logger.info(f"Status command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing status data for {interaction.user}: {e}")
            error_embed = create_embed(command_name="System Status", color="#ef4444")
            error_embed.description = (
                "❌ Error processing status data. Please try again later."
            )
            await message.edit(embed=error_embed)

    def cog_unload(self) -> None:
        import asyncio

        asyncio.create_task(self.session.close())
        logger.info("StatusCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatusCommands(bot))
    logger.info("StatusCommands cog loaded")
