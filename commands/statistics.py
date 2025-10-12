import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from modules.embeds import create_embed


class HeatLabsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.stats_url = "https://views.heatlabs.net/api/stats"
        self.pixel_config_url = "https://cdn.jsdelivr.net/gh/PCWStats/Website-Configs@main/tracking-pixel.json"
        self.heatlabs_url = "https://heatlabs.net"
        self.cache: Dict[str, Any] = {
            "stats": None,
            "pixel_config": None,
            "last_updated": None,
        }

    async def fetch_data(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                logging.error(
                    f"Failed to fetch data from {url}: HTTP {response.status}"
                )
                return None
        except Exception as e:
            logging.error(f"Error fetching data from {url}: {e}")
            return None

    # Fetch fresh data from both APIs and update cache
    async def refresh_cache(self) -> bool:
        try:
            # Fetch both data sources concurrently
            stats, pixel_config = await asyncio.gather(
                self.fetch_data(self.stats_url), self.fetch_data(self.pixel_config_url)
            )

            if stats is None or pixel_config is None:
                logging.error("Failed to fetch one or more data sources")
                return False

            self.cache["stats"] = stats
            self.cache["pixel_config"] = pixel_config
            self.cache["last_updated"] = datetime.utcnow()
            logging.info("HEAT labs cache refreshed successfully")
            return True
        except Exception as e:
            logging.error(f"Error refreshing HEAT Labs cache: {e}")
            return False

    # Get the human-readable page name from the pixel filename
    def get_page_name(self, pixel_filename: str) -> str:
        if not self.cache["pixel_config"]:
            return pixel_filename

        for pixel in self.cache["pixel_config"].get("pixels", []):
            if pixel.get("pixel_filename") == pixel_filename:
                return pixel.get("page_name", pixel_filename)

        return pixel_filename

    def calculate_stats(self, stats_data: Dict[str, Any]) -> Dict[str, Any]:
        total_views = 0
        thirty_day_views = 0
        top_pages: List[Dict[str, Any]] = []
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        for pixel_filename, data in stats_data.items():
            # Calculate total views
            pixel_total = data.get("totalViews", 0)
            total_views += pixel_total

            # Calculate 30-day views
            pixel_daily = data.get("dailyViews", {})
            pixel_thirty_day = 0
            for date_str, views in pixel_daily.items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if date >= thirty_days_ago:
                        pixel_thirty_day += views
                except:
                    continue
            thirty_day_views += pixel_thirty_day

            # Prepare for top pages
            page_name = self.get_page_name(pixel_filename)
            top_pages.append(
                {
                    "name": page_name,
                    "total": pixel_total,
                    "recent": pixel_thirty_day,
                    "pixel": pixel_filename,
                }
            )

        # Sort by total views descending
        top_pages.sort(key=lambda x: x["total"], reverse=True)

        return {
            "total_views": total_views,
            "thirty_day_views": thirty_day_views,
            "top_pages": top_pages[:10],  # Only keep top 10
        }

    @app_commands.command(
        name="statistics",
        description="Get real-time statistics about HEAT Labs website traffic",
    )
    async def heatlabs(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        # Create embed with standardized header
        embed = create_embed(command_name="Statistics", color="#ff8300")

        success = await self.refresh_cache()

        if not success:
            embed.description = "⚠️ Failed to fetch fresh data from HEAT Labs API. Please try again later."
            await interaction.followup.send(embed=embed)
            return

        try:
            if not self.cache["stats"] or not self.cache["pixel_config"]:
                embed.description = "⚠️ Received incomplete data from HEAT Labs API."
                await interaction.followup.send(embed=embed)
                return

            stats = self.calculate_stats(self.cache["stats"])

            # Add main statistics
            embed.add_field(
                name="📈 Overall Statistics",
                value=f"**Total Lifetime Views:** {stats['total_views']:,}\n"
                f"**Last 30 Days Views:** {stats['thirty_day_views']:,}",
                inline=False,
            )

            # Add top pages
            top_pages_text = []
            for i, page in enumerate(stats["top_pages"], 1):
                top_pages_text.append(
                    f"{i}. **{page['name']}** - {page['total']:,} views "
                    f"({page['recent']:,} recent)"
                )

            embed.add_field(
                name="🏆 Top 10 Pages",
                value="\n".join(top_pages_text) or "No data available",
                inline=False,
            )

            # Add data freshness info
            if self.cache["last_updated"]:
                embed.add_field(
                    name="🕐 Data Freshness",
                    value=f"Last updated: {self.cache['last_updated'].strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    inline=False,
                )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logging.error(f"Error processing HEAT Labs data: {e}")
            embed.description = (
                "⚠️ Error processing HEAT Labs data. Please try again later."
            )
            await interaction.followup.send(embed=embed)

    def cog_unload(self) -> None:
        asyncio.create_task(self.session.close())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HeatLabsCommands(bot))
