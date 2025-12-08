import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
from typing import Optional
from modules.embeds import create_embed, add_embed_footer
from modules.logger import get_logger

logger = get_logger()


class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.help_url = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/help.json"
        self.commands_per_page = 10

    # Fetch help data from JSON file
    async def fetch_help_data(self):
        try:
            async with self.session.get(self.help_url) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    logger.info("Help data fetched successfully")
                    return data
                logger.warning(f"Failed to fetch help data: HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching help data: {e}")
            return None

    # Organize commands by category and prepare pagination
    def organize_commands_by_category(self, commands_data: list):
        # Group commands by category
        categories = {}
        for cmd in commands_data:
            category = cmd["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(cmd)

        # Sort categories alphabetically
        sorted_categories = sorted(categories.items())

        # Create pages with complete categories
        pages = []
        current_page_commands = []
        current_page_char_count = 0

        for category, category_commands in sorted_categories:
            # Calculate how much space this category would take
            category_header = f"📚 {category}\n"
            category_commands_text = []
            category_char_count = len(category_header)

            for cmd in category_commands:
                cmd_text = f"**`/{cmd['name']}`** - {cmd['description']}\n"
                category_char_count += len(cmd_text)
                category_commands_text.append(cmd_text)

            # Add tips section space (approximately 250 chars for tips)
            tips_char_count = 250 if not current_page_commands else 0

            # Check if this category fits on the current page
            if (
                current_page_char_count + category_char_count + tips_char_count
            ) <= 4000 and len(current_page_commands) + len(category_commands) <= 20:
                # Add category to current page
                current_page_commands.extend(category_commands)
                current_page_char_count += category_char_count
            else:
                # Save current page and start new one
                if current_page_commands:
                    pages.append(current_page_commands)
                # Start new page with this category
                current_page_commands = category_commands
                current_page_char_count = category_char_count

        # Add the last page
        if current_page_commands:
            pages.append(current_page_commands)

        return pages

    # Create a help page embed with the given commands
    async def create_help_page(
        self, page_commands: list, page: int, total_pages: int
    ) -> discord.Embed:
        # Create the embed
        embed = create_embed(command_name="Help", color="#ff8300")

        # Group commands on this page by category
        categories_on_page = {}
        for cmd in page_commands:
            category = cmd["category"]
            if category not in categories_on_page:
                categories_on_page[category] = []
            categories_on_page[category].append(cmd)

        # Sort categories alphabetically
        sorted_categories = sorted(categories_on_page.items())

        # Add each category to the embed
        for category, category_commands in sorted_categories:
            # Format the commands for this category
            command_list = []
            for cmd in category_commands:
                command_list.append(f"**`/{cmd['name']}`** – {cmd['description']}")

            # Add category field
            embed.add_field(
                name=f"📚 {category}", value="\n".join(command_list), inline=False
            )

        # Add tips section
        embed.add_field(
            name="💡 Tips",
            value=(
                "• Use `/help [page]` to navigate between pages\n"
                "• Command names are case-insensitive\n"
                "• For more information, visit the bot's [documentation](https://bot.heatlabs.net)"
            ),
            inline=False,
        )

        # Add page indicator
        embed.description = f"**Page {page} of {total_pages}**\n\n"

        return embed

    @app_commands.command(
        name="help",
        description="View all available HEAT Labs bot commands",
    )
    @app_commands.describe(page="Page number to view (optional)")
    async def help(
        self, interaction: discord.Interaction, page: Optional[int] = 1
    ) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Help command invoked by {interaction.user} in guild {interaction.guild.name} (Page: {page})"
        )

        # Fetch help data
        help_data = await self.fetch_help_data()

        if not help_data:
            embed = create_embed(command_name="Help", color="#ff8300")
            embed.description = "⚠️ Failed to load help data. Please try again later."
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Help command failed: Unable to fetch help data for {interaction.user}"
            )
            return

        try:
            commands_list = help_data.get("commands", [])

            if not commands_list:
                embed = create_embed(command_name="Help", color="#ff8300")
                embed.description = "⚠️ No commands available in the help system."
                embed = add_embed_footer(embed)
                await interaction.followup.send(embed=embed)
                logger.warning(f"No commands found in help data for {interaction.user}")
                return

            # Organize commands into pages with complete categories
            pages = self.organize_commands_by_category(commands_list)
            total_pages = len(pages)

            # Validate page number
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages

            # Get commands for the requested page
            page_commands = pages[page - 1]

            # Create the help page
            embed = await self.create_help_page(page_commands, page, total_pages)

            # Add the standardized footer
            embed = add_embed_footer(embed)

            # Send the embed
            await interaction.followup.send(embed=embed)
            logger.info(
                f"Help command completed successfully for {interaction.user} (Page {page}/{total_pages})"
            )

        except Exception as e:
            logger.error(f"Error processing help command for {interaction.user}: {e}")
            embed = create_embed(command_name="Help", color="#ff8300")
            embed.description = "⚠️ Error loading help menu. Please try again later."
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)

    # Autocomplete for page numbers
    @help.autocomplete("page")
    async def page_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            help_data = await self.fetch_help_data()
            if not help_data:
                return []

            commands_list = help_data.get("commands", [])
            if not commands_list:
                return []

            # Organize commands into pages
            pages = self.organize_commands_by_category(commands_list)
            total_pages = len(pages)

            # Create page suggestions
            suggestions = []
            for page_num in range(
                1, min(total_pages + 1, 6)
            ):  # Limit to first 5 pages for autocomplete
                page_text = f"{page_num}"
                if current:
                    if current.lower() in page_text.lower() or current == str(page_num):
                        suggestions.append(
                            app_commands.Choice(name=page_text, value=page_num)
                        )
                else:
                    suggestions.append(
                        app_commands.Choice(name=page_text, value=page_num)
                    )

            return suggestions[:25]  # Discord limit

        except Exception as e:
            logger.error(f"Error in page autocomplete: {e}")
            return []


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommands(bot))
    logger.info("HelpCommands cog loaded")
