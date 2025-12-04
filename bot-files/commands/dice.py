import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from typing import Dict, List
from modules.embeds import create_embed
from modules.logger import get_logger

logger = get_logger()


class DiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = "config/dice_roll.json"

    # Load dice roll statistics from JSON file
    def load_stats(self) -> Dict:
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                    logger.debug("Dice stats loaded successfully")
                    return data
            logger.info(f"Dice stats file not found, creating new: {self.stats_file}")
            return {"servers": {}}
        except Exception as e:
            logger.error(f"Error loading dice stats: {e}")
            return {"servers": {}}

    def save_stats(self, stats: Dict) -> None:
        """Save dice roll statistics to JSON file."""
        try:
            with open(self.stats_file, "w") as f:
                json.dump(stats, f, indent=2)
            logger.debug("Dice stats saved successfully")
        except Exception as e:
            logger.error(f"Error saving dice stats: {e}")

    # Generate a random number between 1 and 10
    def generate_dice_number(self) -> int:
        return random.randint(1, 10)

    def update_user_stats(
        self, user_id: str, username: str, guild_id: str, is_correct: bool
    ) -> Dict:
        stats = self.load_stats()

        # Initialize server entry if it doesn't exist
        if guild_id not in stats["servers"]:
            stats["servers"][guild_id] = []

        # Find or create user entry in server
        user_found = False
        for user in stats["servers"][guild_id]:
            if user["user_id"] == user_id:
                user_found = True
                if is_correct:
                    user["correct_guesses"] = user.get("correct_guesses", 0) + 1
                else:
                    user["wrong_guesses"] = user.get("wrong_guesses", 0) + 1
                user["total_guesses"] = user.get("total_guesses", 0) + 1
                user["username"] = username
                break

        if not user_found:
            new_user = {
                "user_id": user_id,
                "username": username,
                "correct_guesses": 1 if is_correct else 0,
                "wrong_guesses": 0 if is_correct else 1,
                "total_guesses": 1,
            }
            stats["servers"][guild_id].append(new_user)

        self.save_stats(stats)
        return self.get_user_stats(stats, user_id, guild_id)

    # Get user statistics from loaded stats
    def get_user_stats(self, stats: Dict, user_id: str, guild_id: str) -> Dict:
        user_stats = {
            "global_correct": 0,
            "global_wrong": 0,
            "global_total": 0,
            "global_ratio": 0.0,
            "server_correct": 0,
            "server_wrong": 0,
            "server_total": 0,
            "server_ratio": 0.0,
        }

        # Calculate global stats by aggregating across all servers
        for server_id, users in stats.get("servers", {}).items():
            for user in users:
                if user["user_id"] == user_id:
                    user_stats["global_correct"] += user.get("correct_guesses", 0)
                    user_stats["global_wrong"] += user.get("wrong_guesses", 0)
                    user_stats["global_total"] += user.get("total_guesses", 0)

        # Calculate global ratio
        if user_stats["global_total"] > 0:
            user_stats["global_ratio"] = (
                user_stats["global_correct"] / user_stats["global_total"]
            )

        # Find server-specific stats
        if guild_id in stats.get("servers", {}):
            for user in stats["servers"][guild_id]:
                if user["user_id"] == user_id:
                    user_stats["server_correct"] = user.get("correct_guesses", 0)
                    user_stats["server_wrong"] = user.get("wrong_guesses", 0)
                    user_stats["server_total"] = user.get("total_guesses", 0)
                    if user_stats["server_total"] > 0:
                        user_stats["server_ratio"] = (
                            user_stats["server_correct"] / user_stats["server_total"]
                        )
                    break

        return user_stats

    # Get user's global rank based on ratio
    def get_global_rank(self, user_id: str) -> int:
        stats = self.load_stats()

        # Aggregate user data from all servers
        user_aggregates = {}
        for server_id, users in stats.get("servers", {}).items():
            for user in users:
                uid = user["user_id"]
                if uid not in user_aggregates:
                    user_aggregates[uid] = {
                        "username": user.get("username", "Unknown"),
                        "correct": 0,
                        "total": 0,
                        "ratio": 0.0,
                    }
                user_aggregates[uid]["correct"] += user.get("correct_guesses", 0)
                user_aggregates[uid]["total"] += user.get("total_guesses", 0)

        # Calculate ratios
        user_ratios = []
        for uid, data in user_aggregates.items():
            ratio = data["correct"] / data["total"] if data["total"] > 0 else 0.0
            user_ratios.append((uid, ratio, data["total"]))

        if not user_ratios:
            return 1

        # Sort by ratio (descending), then by total guesses (descending)
        sorted_users = sorted(user_ratios, key=lambda x: (x[1], x[2]), reverse=True)

        # Find user's rank (1-indexed)
        for i, (uid, _, _) in enumerate(sorted_users, 1):
            if uid == user_id:
                return i

        return len(sorted_users) + 1  # User not in list

    # Get user's server rank based on ratio
    def get_server_rank(self, user_id: str, guild_id: str) -> int:
        stats = self.load_stats()

        if guild_id not in stats.get("servers", {}):
            return 1  # Only user in server

        server_users = stats["servers"][guild_id]

        if not server_users:
            return 1

        # Calculate ratio for each user
        user_ratios = []
        for user in server_users:
            total = user.get("total_guesses", 0)
            correct = user.get("correct_guesses", 0)
            ratio = correct / total if total > 0 else 0.0
            user_ratios.append((user["user_id"], ratio, total))

        # Sort by ratio (descending), then by total guesses (descending)
        sorted_users = sorted(user_ratios, key=lambda x: (x[1], x[2]), reverse=True)

        # Find user's rank (1-indexed)
        for i, (uid, _, _) in enumerate(sorted_users, 1):
            if uid == user_id:
                return i

        return len(sorted_users) + 1  # User not in list

    # Get top users globally
    def get_top_global(self, limit: int = 5) -> List[Dict]:
        stats = self.load_stats()

        # Aggregate user data from all servers
        user_aggregates = {}
        for server_id, users in stats.get("servers", {}).items():
            for user in users:
                uid = user["user_id"]
                if uid not in user_aggregates:
                    user_aggregates[uid] = {
                        "username": user.get("username", "Unknown"),
                        "correct": 0,
                        "wrong": 0,
                        "total": 0,
                        "ratio": 0.0,
                    }
                user_aggregates[uid]["correct"] += user.get("correct_guesses", 0)
                user_aggregates[uid]["wrong"] += user.get("wrong_guesses", 0)
                user_aggregates[uid]["total"] += user.get("total_guesses", 0)

        # Calculate ratios
        user_data = []
        for uid, data in user_aggregates.items():
            ratio = data["correct"] / data["total"] if data["total"] > 0 else 0.0
            user_data.append(
                {
                    "user_id": uid,
                    "username": data["username"],
                    "correct_guesses": data["correct"],
                    "wrong_guesses": data["wrong"],
                    "total_guesses": data["total"],
                    "ratio": ratio,
                }
            )

        # Sort by ratio (descending), then by total guesses (descending)
        sorted_users = sorted(
            user_data,
            key=lambda x: (x.get("ratio", 0), x.get("total_guesses", 0)),
            reverse=True,
        )

        return sorted_users[:limit]

    # Get top users in a server
    def get_top_server(self, guild_id: str, limit: int = 5) -> List[Dict]:
        stats = self.load_stats()

        if guild_id not in stats.get("servers", {}):
            return []

        server_users = stats["servers"][guild_id]

        # Calculate ratio for each user
        user_data = []
        for user in server_users:
            total = user.get("total_guesses", 0)
            correct = user.get("correct_guesses", 0)
            ratio = correct / total if total > 0 else 0.0
            user_data.append(
                {
                    "user_id": user["user_id"],
                    "username": user.get("username", "Unknown"),
                    "correct_guesses": correct,
                    "wrong_guesses": user.get("wrong_guesses", 0),
                    "total_guesses": total,
                    "ratio": ratio,
                }
            )

        # Sort by ratio (descending), then by total guesses (descending)
        sorted_users = sorted(
            user_data,
            key=lambda x: (x.get("ratio", 0), x.get("total_guesses", 0)),
            reverse=True,
        )

        return sorted_users[:limit]

    def get_custom_response(
        self, user_guess: int, dice_number: int, is_correct: bool
    ) -> str:
        diff = abs(user_guess - dice_number)

        if is_correct:
            responses = [
                "🎯 **BULLSEYE!** You nailed it perfectly!",
                "✨ **INCREDIBLE!** Right on the money!",
                "🏆 **PERFECT GUESS!** You're on fire!",
                "🎲 **SPOT ON!** The dice gods are with you!",
                "💫 **EXACT MATCH!** You're a guessing genius!",
            ]
            return random.choice(responses)

        elif diff == 1:
            responses = [
                "🔥 **SO CLOSE!** Just one away! That's painful!",
                "😱 **ALMOST!** You were off by a single number!",
                "📏 **NEAR MISS!** Just a hair's breadth away!",
                "⚡ **CLOSE CALL!** The dice almost obeyed you!",
                "🎯 **ALMOST PERFECT!** You can taste the victory!",
            ]
            return random.choice(responses)

        elif diff == 2:
            responses = [
                "🎲 **TWO OFF!** You’re circling the target!",
                "🔥 **NOT FAR!** Just a couple steps away!",
                "😎 **SOLID TRY!** You're hovering around the sweet spot!",
                "📉 **JUST A BIT OUT!** Close enough to keep hope alive!",
                "⚙️ **ALMOST THERE!** A tiny adjustment and you’d nail it!",
            ]
            return random.choice(responses)

        elif diff <= 3:
            responses = [
                "😅 **NOT BAD!** You were in the right neighborhood!",
                "🤏 **PRETTY CLOSE!** Warming up those dice skills!",
                "📊 **GOOD TRY!** Getting warmer with each roll!",
                "🎯 **DECENT SHOT!** You're honing your intuition!",
                "✨ **CLOSE ENOUGH!** The dice felt your presence!",
            ]
            return random.choice(responses)

        elif diff == 4:
            responses = [
                "🌬️ **DRIFTING AWAY!** A bit wide, but still respectable!",
                "🧐 **HMM…** Not the closest, but not terrible either!",
                "🎲 **A LITTLE FAR!** Dice had their own opinion this time!",
                "📏 **WIDE GAP!** You’re outside the comfort zone now!",
                "🌀 **OFF BY FOUR!** The dice took a scenic route!",
            ]
            return random.choice(responses)

        elif diff == 5:
            responses = [
                "🌪️ **WAY OUT THERE!** The dice went on vacation!",
                "😬 **FAR FROM IT!** But hey, it happens!",
                "🎯 **NOT EVEN CLOSE!** Fresh start needed!",
                "📉 **BIG MISS!** The dice chose chaos today!",
                "🤷 **FIVE OFF!** RNG said ‘nope.’",
            ]
            return random.choice(responses)

        else:
            responses = [
                "😬 **NOT QUITE!** Better luck next time!",
                "🎲 **MISSED IT!** The dice have spoken!",
                "🔄 **TRY AGAIN!** Your luck will turn around!",
                "🤔 **NICE TRY!** The numbers can be tricky!",
                "🎯 **OFF TARGET!** But don't give up!",
            ]
            return random.choice(responses)

    @app_commands.command(
        name="dice-roll", description="Roll the dice and guess the number! (1-10)"
    )
    @app_commands.describe(guess="Your guess between 1 and 10")
    async def dice_roll(self, interaction: discord.Interaction, guess: int) -> None:
        # Validate guess
        if guess < 1 or guess > 10:
            embed = create_embed(
                command_name="Dice Roll",
                description="❌ Please guess a number between 1 and 10!",
                color="#ef4444",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.warning(f"Invalid guess {guess} by {interaction.user}")
            return

        # Defer the response
        await interaction.response.defer()

        try:
            # Generate dice number
            dice_number = self.generate_dice_number()
            is_correct = guess == dice_number

            # Update stats
            user_stats = self.update_user_stats(
                user_id=str(interaction.user.id),
                username=str(interaction.user),
                guild_id=str(interaction.guild.id),
                is_correct=is_correct,
            )

            # Get ranks
            global_rank = self.get_global_rank(str(interaction.user.id))
            server_rank = self.get_server_rank(
                str(interaction.user.id), str(interaction.guild.id)
            )

            # Create embed
            color = "#22c55e" if is_correct else "#ef4444"
            embed = create_embed(command_name="Dice Roll", color=color)

            # Add result
            embed.add_field(
                name="🎲 Dice Result",
                value=f"**Your Guess:** {guess}\n**Dice Roll:** {dice_number}",
                inline=False,
            )

            # Add custom response
            custom_response = self.get_custom_response(guess, dice_number, is_correct)
            embed.add_field(name="🎯 Result", value=custom_response, inline=False)

            # Add stats
            stats_text = (
                f"✅ Correct Guesses: {user_stats['global_correct']}\n"
                f"❌ Wrong Guesses: {user_stats['global_wrong']}\n"
                f"📊 Win Ratio: {user_stats['global_ratio']:.1%}\n"
                f"🌍 Global Rank: #{global_rank}\n"
                f"🏢 Server Rank: #{server_rank}"
            )

            embed.add_field(name="Your Statistics:", value=stats_text, inline=False)

            logger.info(
                f"Dice roll by {interaction.user}: guess={guess}, dice={dice_number}, "
                f"correct={is_correct}, guild={interaction.guild.name}"
            )

            # Send the followup message
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in dice_roll command: {e}")
            error_embed = create_embed(
                command_name="Dice Roll",
                description="❌ An error occurred while processing your dice roll. Please try again.",
                color="#ef4444",
            )
            await interaction.followup.send(embed=error_embed)

    @app_commands.command(
        name="dice-rank", description="Check your dice rolling ranks and leaderboards"
    )
    async def dice_rank(self, interaction: discord.Interaction) -> None:
        # Defer the response
        await interaction.response.defer()

        try:
            embed = create_embed(command_name="Dice Rank", color="#ff8300")

            # Get user stats
            stats = self.load_stats()
            user_stats = self.get_user_stats(
                stats, str(interaction.user.id), str(interaction.guild.id)
            )

            # Get ranks
            global_rank = self.get_global_rank(str(interaction.user.id))
            server_rank = self.get_server_rank(
                str(interaction.user.id), str(interaction.guild.id)
            )

            # User's stats section
            user_stats_text = (
                f"✅ Correct Guesses: {user_stats['global_correct']}\n"
                f"❌ Wrong Guesses: {user_stats['global_wrong']}\n"
                f"📊 Win Ratio: {user_stats['global_ratio']:.1%}\n"
                f"🌍 Global Rank: #{global_rank}\n"
                f"🏢 Server Rank: #{server_rank}"
            )

            embed.add_field(
                name=f"🎲 {interaction.user.name}'s Rankings",
                value=user_stats_text,
                inline=False,
            )

            # Get top 5 global
            top_global = self.get_top_global(5)
            if top_global:
                global_text = ""
                for i, user in enumerate(top_global, 1):
                    ratio = user.get("ratio", 0)
                    correct = user.get("correct_guesses", 0)
                    wrong = user.get("wrong_guesses", 0)
                    username = user.get("username", "Unknown")

                    # Truncate long usernames
                    if len(username) > 20:
                        username = username[:17] + "..."

                    global_text += (
                        f"**#{i} {username}**\n"
                        f"✅ {correct} | ❌ {wrong} | 📊 {ratio:.1%}\n"
                    )

                embed.add_field(
                    name="🌍 Top 5 Global",
                    value=global_text if global_text else "*No data yet*",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="🌍 Top 5 Global",
                    value="*No data yet, be the first to roll!*",
                    inline=False,
                )

            # Get top 5 server
            top_server = self.get_top_server(str(interaction.guild.id), 5)
            if top_server:
                server_text = ""
                for i, user in enumerate(top_server, 1):
                    ratio = user.get("ratio", 0)
                    correct = user.get("correct_guesses", 0)
                    wrong = user.get("wrong_guesses", 0)
                    username = user.get("username", "Unknown")

                    # Truncate long usernames
                    if len(username) > 20:
                        username = username[:17] + "..."

                    server_text += (
                        f"**#{i} {username}**\n"
                        f"✅ {correct} | ❌ {wrong} | 📊 {ratio:.1%}\n"
                    )

                embed.add_field(
                    name=f"🏢 Top 5 in {interaction.guild.name}",
                    value=server_text if server_text else "*No data yet*",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"🏢 Top 5 in {interaction.guild.name}",
                    value="*No data yet, roll the dice to get on the board!*",
                    inline=False,
                )

            logger.info(
                f"Dice rank command by {interaction.user} in guild {interaction.guild.name}"
            )

            # Send the followup message
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in dice_rank command: {e}")
            error_embed = create_embed(
                command_name="Dice Rank",
                description="❌ An error occurred while fetching rankings. Please try again.",
                color="#ef4444",
            )
            await interaction.followup.send(embed=error_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceCommands(bot))
    logger.info("DiceCommands cog loaded")
