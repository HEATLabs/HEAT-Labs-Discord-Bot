import json
import os
from datetime import datetime
import discord
from modules.logger import get_logger

logger = get_logger()


class ServerTracker:
    def __init__(self):
        self.config_dir = "config"
        self.servers_file = os.path.join(self.config_dir, "servers.json")
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            logger.info(f"Created {self.config_dir} directory")

        if not os.path.exists(self.servers_file):
            self._write_servers([])
            logger.info(f"Created {self.servers_file}")

    def _read_servers(self) -> list:
        try:
            with open(self.servers_file, "r") as f:
                data = json.load(f)
                return data.get("servers", [])
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Error reading servers file: {self.servers_file}")
            return []

    def _write_servers(self, servers: list):
        try:
            data = {"servers": servers}
            with open(self.servers_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Servers file written: {len(servers)} entries")
        except Exception as e:
            logger.error(f"Error writing servers file: {e}")

    def sync_servers(self, guilds: list):
        current_servers = self._read_servers()
        current_ids = {server["id"] for server in current_servers}
        current_guild_ids = {guild.id for guild in guilds}

        # Add any new servers that are not in the file
        added_count = 0
        for guild in guilds:
            if guild.id not in current_ids:
                self._add_server_internal(guild, current_servers)
                added_count += 1
                logger.info(f"Added to server list: {guild.name} (ID: {guild.id})")
            else:
                # Update existing server's member count
                self._update_server_member_count(guild, current_servers)

        # Remove servers that the bot is no longer in
        removed_count = 0
        updated_servers = []
        for server in current_servers:
            if server["id"] in current_guild_ids:
                updated_servers.append(server)
            else:
                removed_count += 1
                logger.info(
                    f"Removed from server list: {server['name']} (ID: {server['id']})"
                )

        if added_count > 0 or removed_count > 0:
            self._write_servers(updated_servers)
            logger.info(
                f"Server sync complete: {added_count} added, {removed_count} removed"
            )
        else:
            logger.info("Server sync complete: No changes needed")

    def _add_server_internal(self, guild: discord.Guild, servers_list: list):
        server_entry = {
            "name": guild.name,
            "id": guild.id,
            "date_added": datetime.now().isoformat(),
            "member_count": guild.member_count,
            "last_updated": datetime.now().isoformat(),
        }
        servers_list.append(server_entry)

    def _update_server_member_count(self, guild: discord.Guild, servers_list: list):
        for server in servers_list:
            if server["id"] == guild.id:
                server["member_count"] = guild.member_count
                server["last_updated"] = datetime.now().isoformat()
                logger.debug(
                    f"Updated member count for {guild.name}: {guild.member_count}"
                )
                break

    def add_server(self, guild: discord.Guild):
        servers = self._read_servers()

        # Check if server already exists
        existing_server = next((s for s in servers if s["id"] == guild.id), None)
        if existing_server:
            # Update member count for existing server
            existing_server["member_count"] = guild.member_count
            existing_server["last_updated"] = datetime.now().isoformat()
            self._write_servers(servers)
            logger.info(
                f"Updated member count for existing server: {guild.name} (ID: {guild.id})"
            )
            return True

        self._add_server_internal(guild, servers)
        self._write_servers(servers)
        logger.info(f"Added to server list: {guild.name} (ID: {guild.id})")
        return True

    def remove_server(self, guild_id: int):
        servers = self._read_servers()
        initial_count = len(servers)
        updated_servers = [s for s in servers if s["id"] != guild_id]

        if len(updated_servers) < initial_count:
            self._write_servers(updated_servers)
            logger.info(f"Removed server from list: {guild_id}")
            return True
        return False

    def update_all_member_counts(self, guilds: list):
        servers = self._read_servers()
        updated_count = 0

        for server in servers:
            # Find matching guild
            matching_guild = next((g for g in guilds if g.id == server["id"]), None)
            if matching_guild:
                server["member_count"] = matching_guild.member_count
                server["last_updated"] = datetime.now().isoformat()
                updated_count += 1

        if updated_count > 0:
            self._write_servers(servers)
            logger.info(f"Updated member counts for {updated_count} servers")
            return updated_count
        return 0

    def get_servers(self) -> list:
        return self._read_servers()

    def get_server(self, guild_id: int) -> dict:
        servers = self._read_servers()
        return next((s for s in servers if s["id"] == guild_id), None)

    # Calculate total members across all tracked servers
    def get_total_members(self) -> int:
        servers = self._read_servers()
        return sum(server.get("member_count", 0) for server in servers)
