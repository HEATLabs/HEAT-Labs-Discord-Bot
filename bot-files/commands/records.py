import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import re
from modules.embeds import create_embed, add_embed_footer
from modules.logger import get_logger

logger = get_logger()

# Constants
RECORDS_URL = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/player-records.json"

# Mode choices
MODES = [
    ("global", "Global"),
    ("conquest", "Conquest"),
    ("control", "Control"),
    ("hardpoint", "Hardpoint"),
    ("kill-confirmed", "Kill Confirmed"),
]

# Stat categories with their display names
CATEGORIES = {
    "damage_caused": {"label": "Damage Dealt"},
    "destroyed": {"label": "Kills"},
    "assists": {"label": "Assists"},
    "XP": {"label": "Experience"},
    "captures": {"label": "Captures"},
    "damage_blocked": {"label": "Damage Blocked"},
    "credits": {"label": "Credits Earned"},
    "intel": {"label": "Intel"},
    "confirms": {"label": "Confirms"},
    "denies": {"label": "Denies"},
}

# Mode-specific stat availability
MODE_STATS = {
    "global": list(CATEGORIES.keys()),
    "conquest": ["damage_caused", "destroyed", "assists", "XP", "captures", "damage_blocked", "credits", "intel"],
    "control": ["damage_caused", "destroyed", "assists", "XP", "captures", "damage_blocked", "credits", "intel"],
    "hardpoint": ["damage_caused", "destroyed", "assists", "XP", "captures", "damage_blocked", "credits", "intel"],
    "kill-confirmed": ["damage_caused", "destroyed", "assists", "XP", "confirms", "denies", "credits", "intel"],
}

# Mode display names
MODE_DISPLAY = {
    "global": "Global",
    "conquest": "Conquest",
    "control": "Control",
    "hardpoint": "Hardpoint",
    "kill-confirmed": "Kill Confirmed",
}


class RecordsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.records_data = None
        self.last_fetch_time = 0

    async def fetch_records_data(self):
        """Fetch records data with caching (5 minute TTL)"""
        import time
        current_time = time.time()

        # Cache for 5 minutes
        if self.records_data and (current_time - self.last_fetch_time < 300):
            return self.records_data

        try:
            async with self.session.get(RECORDS_URL) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    self.records_data = data
                    self.last_fetch_time = current_time
                    logger.info("Records data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch records data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching records data: {e}")
            return None

    def get_mode_records(self, data, mode):
        """Get records for a specific mode"""
        if mode == "global":
            # Combine all modes
            all_records = []
            for m in ["conquest", "control", "hardpoint", "kill-confirmed"]:
                if m in data.get("records", {}):
                    mode_records = data["records"].get(m, {})
                    for player_id, player_records in mode_records.items():
                        for record in player_records:
                            record_copy = record.copy()
                            record_copy["_mode"] = m
                            record_copy["_player_id"] = player_id
                            all_records.append(record_copy)
            return all_records
        else:
            # Get specific mode
            mode_records = data.get("records", {}).get(mode, {})
            records = []
            for player_id, player_records in mode_records.items():
                for record in player_records:
                    record_copy = record.copy()
                    record_copy["_mode"] = mode
                    record_copy["_player_id"] = player_id
                    records.append(record_copy)
            return records

    def get_top_records(self, records, stat_key, limit=10):
        """Get top records for a specific stat, with each player appearing once"""
        # Group by player, keep highest value
        player_best = {}
        for record in records:
            player_id = record.get("_player_id")
            if not player_id:
                continue
            value = record.get(stat_key, 0)
            if value is None:
                continue
            if player_id not in player_best or value > player_best[player_id]["value"]:
                player_best[player_id] = {
                    "record": record,
                    "value": value
                }

        # Convert to list and sort
        sorted_records = sorted(
            player_best.values(),
            key=lambda x: x["value"],
            reverse=True
        )

        return sorted_records[:limit]

    def format_number(self, num):
        """Format large numbers with K/M suffix"""
        if num is None:
            return "0"
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}K"
        return str(num)

    @app_commands.command(
        name="records",
        description="View top player records filtered by game mode and category"
    )
    @app_commands.describe(
        mode="Select a game mode or 'global' for all modes combined",
        category="Select the stat category to view"
    )
    @app_commands.choices(
        mode=[app_commands.Choice(name=display, value=value) for value, display in MODES],
        category=[
            app_commands.Choice(
                name=info["label"],
                value=key
            )
            for key, info in CATEGORIES.items()
        ]
    )
    async def records(
            self,
            interaction: discord.Interaction,
            mode: app_commands.Choice[str],
            category: app_commands.Choice[str]
    ) -> None:
        await interaction.response.defer(thinking=True)

        mode_value = mode.value
        category_value = category.value
        category_info = CATEGORIES.get(category_value, {"label": category_value})
        category_label = category_info["label"]

        logger.info(
            f"Records command invoked by {interaction.user} "
            f"(mode={mode_value}, category={category_value})"
        )

        # Fetch data
        data = await self.fetch_records_data()
        if not data:
            embed = create_embed(
                title="Records Unavailable",
                description="Failed to fetch records data. Please try again later.",
                color="#EF4444"
            )
            await interaction.followup.send(embed=embed)
            return

        # Get records for the selected mode
        records = self.get_mode_records(data, mode_value)

        if not records:
            embed = create_embed(
                title="No Records Found",
                description=f"No records found for **{MODE_DISPLAY.get(mode_value, mode_value)}** mode.",
                color="#F59E0B"
            )
            await interaction.followup.send(embed=embed)
            return

        # Get top records for the selected category
        top_records = self.get_top_records(records, category_value, 10)

        if not top_records:
            embed = create_embed(
                title="No Records Found",
                description=f"No records found for **{category_label}** in **{MODE_DISPLAY.get(mode_value, mode_value)}** mode.",
                color="#F59E0B"
            )
            await interaction.followup.send(embed=embed)
            return

        # Create the embed
        mode_display = MODE_DISPLAY.get(mode_value, mode_value)
        embed = create_embed(
            title=f"{category_label} Records",
            description=f"Top records in **{mode_display}** mode",
            color="#ff8300"
        )

        # Build the leaderboard with better spacing
        leaderboard_lines = []
        for idx, entry in enumerate(top_records, 1):
            record = entry["record"]
            value = entry["value"]
            player_id = record.get("_player_id", "Unknown")
            vehicle = record.get("vehicle", "N/A")
            agent = record.get("agent", "N/A")
            mode_tag = record.get("_mode", "")

            # Medal symbols for top 3
            medal = ""
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"

            # Format the value with the category name
            formatted_value = f"{self.format_number(value)} {category_label}"

            # Format the entry with better spacing
            if medal:
                entry_text = f"#{idx} {medal} **{player_id}**"
            else:
                entry_text = f"#{idx} **{player_id}**"

            entry_text += f"  •  {formatted_value}"
            entry_text += f"  •  {vehicle}"
            entry_text += f"  •  {agent}"

            # Show mode for global view
            if mode_value == "global" and mode_tag:
                entry_text += f"  •  {MODE_DISPLAY.get(mode_tag, mode_tag)}"

            leaderboard_lines.append(entry_text)

        # Combine all entries with double spacing between each
        leaderboard_text = "\n\n".join(leaderboard_lines)

        # Add the leaderboard as a single field
        embed.add_field(
            name="🏆 Leaderboard",
            value=leaderboard_text,
            inline=False
        )

        # Add standard footer via the module
        embed = add_embed_footer(embed)

        await interaction.followup.send(embed=embed)
        logger.info(f"Records command completed for {interaction.user}")

    def cog_unload(self) -> None:
        import asyncio
        asyncio.create_task(self.session.close())
        logger.info("RecordsCommands cog unloaded")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecordsCommands(bot))
    logger.info("RecordsCommands cog loaded")