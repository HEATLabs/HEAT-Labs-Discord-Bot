import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import requests
from modules.embeds import create_embed, add_embed_footer
from modules.logger import get_logger

logger = get_logger()


class FactsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.facts_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/config/facts.json"
        self.facts = []
        self.load_facts()

    # Load facts from JSON file
    def load_facts(self) -> None:
        try:
            response = requests.get(self.facts_file)
            if response.status_code == 200:
                data = response.json()
                self.facts = data.get("facts", [])
                logger.info(f"Facts data loaded successfully: {len(self.facts)} facts")
            else:
                logger.warning(f"Failed to fetch facts: HTTP {response.status_code}")
                self.facts = []
        except Exception as e:
            logger.error(f"Error loading facts: {e}")
            self.facts = []

    # Get a random fact
    def get_random_fact(self) -> str:
        if not self.facts:
            return None

        fact_entry = random.choice(self.facts)
        return fact_entry.get("fact", "No fact available")

    @app_commands.command(
        name="facts",
        description="Get a random fun fact about HEAT Labs projects and vehicles",
    )
    async def facts(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Random Fact", color="#ff8300")
        logger.info(
            f"Facts command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        # Reload facts to ensure we have the latest data
        self.load_facts()

        if not self.facts:
            embed.description = (
                "⚠️ Failed to load facts data. Please try again later.\n"
                f"*Check if the facts file is accessible at: {self.facts_file}*"
            )
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Facts command failed: No facts loaded for {interaction.user}"
            )
            return

        try:
            random_fact = self.get_random_fact()

            if not random_fact:
                embed.description = "⚠️ No facts available. Please try again later."
                embed = add_embed_footer(embed)
                await interaction.followup.send(embed=embed)
                logger.warning(f"No fact retrieved for {interaction.user}")
                return

            # Create the embed description with a fun fact
            fact_count = len(self.facts)
            embed.description = (
                f"**Did you know?**\n\n"
                f"{random_fact}\n\n"
                f"*📚 There are {fact_count} fun facts our database!*\n"
                f"*Use this command again to get another random fact!*"
            )

            # Add the standardized footer
            embed = add_embed_footer(embed)

            await interaction.followup.send(embed=embed)
            logger.info(f"Facts command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing facts for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error retrieving a random fact. Please try again later."
            )
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FactsCommands(bot))
    logger.info("FactsCommands cog loaded")