import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import requests
from modules.embeds import create_embed, add_embed_footer
from modules.logger import get_logger

logger = get_logger()


class MemesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memes_file = "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/memes.json"
        self.memes = []
        self.load_memes()

    # Load memes from JSON file
    def load_memes(self) -> None:
        try:
            response = requests.get(self.memes_file)
            if response.status_code == 200:
                data = response.json()
                self.memes = data
                logger.info(f"Memes data loaded successfully: {len(self.memes)} memes")
            else:
                logger.warning(f"Failed to fetch memes: HTTP {response.status_code}")
                self.memes = []
        except Exception as e:
            logger.error(f"Error loading memes: {e}")
            self.memes = []

    # Get a random meme
    def get_random_meme(self) -> dict:
        if not self.memes:
            return None

        return random.choice(self.memes)

    @app_commands.command(
        name="memes",
        description="Get a random HEAT Labs meme from our collection",
    )
    async def memes(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        embed = create_embed(command_name="Random Meme", color="#ff8300")
        logger.info(
            f"Memes command invoked by {interaction.user} in guild {interaction.guild.name}"
        )

        # Reload memes to ensure we have the latest data
        self.load_memes()

        if not self.memes:
            embed.description = (
                "⚠️ Failed to load memes data. Please try again later.\n"
                f"*Check if the memes file is accessible at: {self.memes_file}*"
            )
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)
            logger.warning(
                f"Memes command failed: No memes loaded for {interaction.user}"
            )
            return

        try:
            random_meme = self.get_random_meme()

            if not random_meme:
                embed.description = "⚠️ No memes available. Please try again later."
                embed = add_embed_footer(embed)
                await interaction.followup.send(embed=embed)
                logger.warning(f"No meme retrieved for {interaction.user}")
                return

            # Get meme details
            meme_name = random_meme.get("name", "Untitled Meme")
            meme_author = random_meme.get("author", "Unknown Author")
            meme_image_url = random_meme.get("path", "")

            # Create the embed description with meme information
            meme_count = len(self.memes)
            embed.description = (
                f"**{meme_name}**\n"
                f"*Created by: {meme_author}*\n\n"
                f"*📚 There are {meme_count} memes in our database!*\n"
                f"*Use this command again to get another random meme!*"
            )

            # Add the meme image if URL is available
            if meme_image_url:
                embed.set_image(url=meme_image_url)
            else:
                embed.add_field(
                    name="⚠️ Image Missing",
                    value="The meme image URL is not available.",
                    inline=False,
                )

            # Add the standardized footer
            embed = add_embed_footer(embed)

            await interaction.followup.send(embed=embed)
            logger.info(f"Memes command completed successfully for {interaction.user}")

        except Exception as e:
            logger.error(f"Error processing memes for {interaction.user}: {e}")
            embed.description = (
                "⚠️ Error retrieving a random meme. Please try again later."
            )
            embed = add_embed_footer(embed)
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemesCommands(bot))
    logger.info("MemesCommands cog loaded")
