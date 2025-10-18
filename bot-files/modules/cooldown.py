import discord
from discord.ext import commands
import os
import time
from modules.logger import get_logger

logger = get_logger()


class GlobalCooldown:
    def __init__(self):
        self.cooldown_seconds = int(
            os.getenv("COMMAND_COOLDOWN", "15")
        )  # Fallback to 15 seconds
        self.user_cooldowns = {}
        logger.info(
            f"Global cooldown initialized with {self.cooldown_seconds} second cooldown"
        )

    # Check if the user is on cooldown, called automatically by discord.py
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        current_time = time.time()

        # Check if user is on cooldown
        if user_id in self.user_cooldowns:
            last_used = self.user_cooldowns[user_id]
            elapsed = current_time - last_used

            if elapsed < self.cooldown_seconds:
                remaining = self.cooldown_seconds - elapsed

                # Create cooldown embed
                embed = discord.Embed(
                    title="⏰ Command Cooldown",
                    description=f"Please wait {remaining:.1f} seconds before using another command.",
                    color=0xFF8300,
                )
                embed.set_footer(
                    text="© 2025 HEAT Labs | Official Discord App",
                    icon_url="https://raw.githubusercontent.com/HEATlabs/HEAT-Labs-Discord-Bot/main/assets/HEAT%20Labs%20Bot%20Profile%20Image.png",
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(
                    f"Cooldown triggered for user {interaction.user} - {remaining:.1f}s remaining"
                )
                return False

        # Update cooldown and allow command
        self.user_cooldowns[user_id] = current_time
        return True


# Global instance
global_cooldown = GlobalCooldown()
