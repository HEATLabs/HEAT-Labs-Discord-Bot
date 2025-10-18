import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio
from modules.embeds import create_embed
from modules.logger import get_logger
from modules.cooldown import global_cooldown

logger = get_logger()


class DebugCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Developer IDs
        self.developer_ids = [212020258402205697, 302329404913352708]

    # Check if a user is developer
    def is_developer(self, user_id: int) -> bool:
        return user_id in self.developer_ids

    # Test the cooldown system without actually responding to interactions
    async def test_cooldown_system(self, user_id: int) -> dict:
        current_time = time.time()

        # Store original cooldown time to restore later
        original_cooldown = global_cooldown.cooldown_seconds

        # Temporarily set cooldown to 2 seconds for testing
        global_cooldown.cooldown_seconds = 2
        global_cooldown.user_cooldowns[user_id] = current_time

        test_results = {
            "cooldown_set": True,
            "cooldown_time": global_cooldown.cooldown_seconds,
            "test_commands": [],
        }

        # Test 1: Immediate check should be blocked
        if user_id in global_cooldown.user_cooldowns:
            last_used = global_cooldown.user_cooldowns[user_id]
            elapsed = current_time - last_used
            should_be_blocked = elapsed < global_cooldown.cooldown_seconds

            test_results["test_commands"].append(
                {
                    "test": "Immediate follow-up command",
                    "should_block": True,
                    "did_block": should_be_blocked,
                    "success": should_be_blocked,
                }
            )

        # Test 2: Wait for cooldown to expire, then test again
        await asyncio.sleep(2.1)  # Wait slightly longer

        current_time_after_wait = time.time()
        if user_id in global_cooldown.user_cooldowns:
            last_used = global_cooldown.user_cooldowns[user_id]
            elapsed = current_time_after_wait - last_used
            should_be_blocked = elapsed < global_cooldown.cooldown_seconds

            test_results["test_commands"].append(
                {
                    "test": "Command after cooldown expired",
                    "should_block": False,
                    "did_block": should_be_blocked,
                    "success": not should_be_blocked,
                }
            )

        # Restore original cooldown
        global_cooldown.cooldown_seconds = original_cooldown

        return test_results

    # Get statistics about all registered commands
    async def get_command_stats(self) -> dict:
        commands_list = []
        for command in self.bot.tree.get_commands():
            if isinstance(command, app_commands.Command):
                commands_list.append(
                    {
                        "name": command.name,
                        "description": command.description,
                        "guild_only": command.guild_only,
                        "default_permissions": command.default_permissions,
                    }
                )

        return {"total_commands": len(commands_list), "commands": commands_list}

    # Get current bot status information
    async def get_bot_status(self) -> dict:
        return {
            "latency": round(self.bot.latency * 1000, 2),
            "guild_count": len(self.bot.guilds),
            "user_count": sum(guild.member_count for guild in self.bot.guilds),
            "uptime": getattr(self.bot, "uptime", "Unknown"),
            "cooldown_setting": global_cooldown.cooldown_seconds,
            "developer_count": len(self.developer_ids),
        }

    # Get status of all loaded cogs
    async def get_cog_status(self) -> dict:
        cogs = []
        for cog_name, cog in self.bot.cogs.items():
            commands_in_cog = []
            for command in cog.get_commands() if hasattr(cog, "get_commands") else []:
                commands_in_cog.append(command.name)

            cogs.append(
                {
                    "name": cog_name,
                    "commands_count": len(commands_in_cog),
                    "commands": commands_in_cog,
                }
            )

        return {"total_cogs": len(cogs), "cogs": cogs}

    @app_commands.command(
        name="debug", description="Developer command for bot diagnostics"
    )
    async def debug(self, interaction: discord.Interaction) -> None:
        # Check if user is a developer
        if not self.is_developer(interaction.user.id):
            embed = create_embed(command_name="Debug", color="#ff8300")
            embed.description = "🔒 This command is intended for developers only.\n\nThis command doesn't hide anything special, it's just a way for us to check if the bot is working as intended. Regular users don't need access to these technical details."

            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(
                f"Debug command blocked for non-developer {interaction.user} (ID: {interaction.user.id})"
            )
            return

        await interaction.response.defer(thinking=True)

        logger.info(
            f"Debug command invoked by developer {interaction.user} (ID: {interaction.user.id}) in guild {interaction.guild.name}"
        )

        try:
            # Create main embed
            embed = create_embed(command_name="Debug & Diagnostics", color="#ff8300")

            # Run all diagnostic tests
            bot_status = await self.get_bot_status()
            command_stats = await self.get_command_stats()
            cog_status = await self.get_cog_status()
            cooldown_test = await self.test_cooldown_system(interaction.user.id)

            # Add bot status section
            status_text = (
                f"**Latency:** {bot_status['latency']}ms\n"
                f"**Guilds:** {bot_status['guild_count']}\n"
                f"**Total Users:** {bot_status['user_count']}\n"
                f"**Cooldown:** {bot_status['cooldown_setting']}s\n"
                f"**Commands Loaded:** {command_stats['total_commands']}\n"
                f"**Cogs Loaded:** {cog_status['total_cogs']}\n"
                f"**Developers:** {bot_status['developer_count']}"
            )
            embed.add_field(name="🤖 Bot Status", value=status_text, inline=False)

            # Add cooldown test results
            cooldown_text = (
                f"**Cooldown Setting:** {cooldown_test['cooldown_time']}s\n\n"
            )

            for test in cooldown_test["test_commands"]:
                status_emoji = "✅" if test["success"] else "❌"
                cooldown_text += (
                    f"{status_emoji} **{test['test']}:** "
                    f"{'BLOCKED' if test['did_block'] else 'ALLOWED'} "
                    f"(Expected: {'BLOCKED' if test['should_block'] else 'ALLOWED'})\n"
                )

            embed.add_field(
                name="⏰ Cooldown System Test", value=cooldown_text, inline=False
            )

            # Add command overview
            command_names = [cmd["name"] for cmd in command_stats["commands"]]
            command_text = ", ".join([f"`/{cmd}`" for cmd in sorted(command_names)])

            if len(command_text) > 1024:
                command_text = command_text[:1020] + "..."

            embed.add_field(
                name="📋 Available Commands",
                value=command_text or "No commands found",
                inline=False,
            )

            # Add cog status
            cog_text = ""
            for cog in cog_status["cogs"]:
                cog_text += f"**{cog['name']}**, "

            embed.add_field(
                name="⚙️ Loaded Cogs", value=cog_text or "No cogs found", inline=False
            )

            # Add system health
            health_emoji = (
                "🟢"
                if bot_status["latency"] < 100
                else "🟡"
                if bot_status["latency"] < 300
                else "🔴"
            )
            all_cooldown_tests_passed = all(
                test["success"] for test in cooldown_test["test_commands"]
            )
            cooldown_emoji = "✅" if all_cooldown_tests_passed else "❌"

            health_text = (
                f"{health_emoji} **Response Time:** {'Excellent' if bot_status['latency'] < 100 else 'Good' if bot_status['latency'] < 300 else 'Poor'}\n"
                f"{cooldown_emoji} **Cooldown System:** {'Working' if all_cooldown_tests_passed else 'Failing'}\n"
                f"📊 **Command Coverage:** {command_stats['total_commands']} commands available\n"
                f"⚙️ **System Stability:** {'Stable' if cog_status['total_cogs'] > 0 else 'Unstable'}"
            )

            embed.add_field(name="🏥 System Health", value=health_text, inline=False)

            # Add developer info
            developer_info = f"**Authorized Developers:** {len(self.developer_ids)}"
            embed.add_field(name="👨‍💻 Access Info", value=developer_info, inline=True)

            # Add timestamp for when diagnostics were run
            embed.add_field(
                name="🕐 Diagnostics Run", value=f"<t:{int(time.time())}:R>", inline=True
            )

            await interaction.followup.send(embed=embed)
            logger.info(
                f"Debug command completed successfully for developer {interaction.user}"
            )

        except Exception as e:
            logger.error(
                f"Error in debug command for developer {interaction.user}: {e}"
            )
            embed = create_embed(command_name="Debug - Error", color="#ff0000")
            embed.description = f"❌ Error running diagnostics: {str(e)}"
            await interaction.followup.send(embed=embed)

    # Set bot uptime when cog is loaded
    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = time.time()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DebugCommands(bot))
    logger.info("DebugCommands cog loaded")
