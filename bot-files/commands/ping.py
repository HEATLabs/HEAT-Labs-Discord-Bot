import discord
from discord.ext import commands
from discord import app_commands
import time
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class PingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ping", description="Check the bot's response times and latency"
    )
    async def ping(self, interaction: discord.Interaction) -> None:
        # Record initial time when command is received
        command_start_time = time.time()

        # Send initial response to measure command processing time
        await interaction.response.defer(thinking=True)

        # Calculate command processing time
        command_end_time = time.time()
        command_ping = (command_end_time - command_start_time) * 1000

        # Get Discord API latency
        discord_api_ping = round(self.bot.latency * 1000, 2)

        # Send followup message and measure bot response time
        bot_response_start = time.time()
        embed = create_embed(command_name="Ping", color="#ff8300")

        # Add ping information
        embed.description = "🏓 **Pong!** Here are the current response times:"

        embed.add_field(
            name="📡 Discord API Latency", value=f"`{discord_api_ping}ms`", inline=True
        )

        embed.add_field(name="🤖 Bot Response Time", value="`Measuring...`", inline=True)

        embed.add_field(
            name="⚡ Command Processing", value=f"`{command_ping:.2f}ms`", inline=True
        )

        # Send the initial embed
        message = await interaction.followup.send(embed=embed)

        # Calculate bot response time
        bot_response_end = time.time()
        bot_response_ping = (bot_response_end - bot_response_start) * 1000

        # Update the embed with the actual bot response time
        updated_embed = create_embed(command_name="Ping", color="#ff8300")
        updated_embed.description = "🏓 **Pong!** Here are the current response times:"

        updated_embed.add_field(
            name="📡 Discord API Latency", value=f"`{discord_api_ping}ms`", inline=True
        )

        updated_embed.add_field(
            name="🤖 Bot Response Time",
            value=f"`{bot_response_ping:.2f}ms`",
            inline=True,
        )

        updated_embed.add_field(
            name="⚡ Command Processing", value=f"`{command_ping:.2f}ms`", inline=True
        )

        # Add timestamp for the measurement
        updated_embed.add_field(
            name="⏰ Measurement Time", value=f"<t:{int(time.time())}:R>", inline=False
        )

        # Edit the original message with updated ping
        await message.edit(embed=updated_embed)

        logger.info(
            f"Ping command completed for {interaction.user} - "
            f"API: {discord_api_ping}ms, "
            f"Command: {command_ping:.2f}ms, "
            f"Response: {bot_response_ping:.2f}ms"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PingCommands(bot))
    logger.info("PingCommands cog loaded")
