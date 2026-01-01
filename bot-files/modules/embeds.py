import discord
from datetime import datetime


# Create a standardized embed with HEAT Labs header and footer
def create_embed(
    title: str = None,
    description: str = None,
    color: str = "#ff8300",
    command_name: str = None,
    heatlabs_url: str = "https://heatlabs.net",
) -> discord.Embed:
    # Convert HEX color to integer
    color_int = int(color.lstrip("#"), 16)
    embed = discord.Embed(color=color_int)

    # Add standardized header if command_name is provided
    if command_name:
        embed.title = f"HEAT Labs - {command_name}"
        embed.url = heatlabs_url
    elif title:
        embed.title = title
        embed.url = heatlabs_url

    # Add description if provided
    if description:
        embed.description = description

    # Add footer with timestamp
    embed = add_embed_footer(embed)
    return embed


# Add standardized footer to an embed
def add_embed_footer(embed: discord.Embed) -> discord.Embed:
    embed.set_footer(
        text="© 2026 HEAT Labs | Official Discord App",
        icon_url="https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Discord-Bot/refs/heads/main/bot-files/assets/public-assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
    )
    embed.timestamp = datetime.now()
    return embed
