import json
import os
from datetime import datetime
import discord


class ServerTracker:
    def __init__(self):
        self.config_dir = "config"
        self.servers_file = os.path.join(self.config_dir, "servers.json")
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            print(f"Created {self.config_dir} directory")

        if not os.path.exists(self.servers_file):
            self._write_servers([])
            print(f"Created {self.servers_file}")

    def _read_servers(self) -> list:
        try:
            with open(self.servers_file, "r") as f:
                data = json.load(f)
                return data.get("servers", [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_servers(self, servers: list):
        data = {"servers": servers}
        with open(self.servers_file, "w") as f:
            json.dump(data, f, indent=2)

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
                print(f"Added to server list: {guild.name} (ID: {guild.id})")

        # Remove servers that the bot is no longer in
        removed_count = 0
        updated_servers = []
        for server in current_servers:
            if server["id"] in current_guild_ids:
                updated_servers.append(server)
            else:
                removed_count += 1
                print(
                    f"Removed from server list: {server['name']} (ID: {server['id']})"
                )

        if added_count > 0 or removed_count > 0:
            self._write_servers(updated_servers)
            print(f"Server sync complete: {added_count} added, {removed_count} removed")
        else:
            print("Server sync complete: No changes needed")

    def _add_server_internal(self, guild: discord.Guild, servers_list: list):
        server_entry = {
            "name": guild.name,
            "id": guild.id,
            "date_added": datetime.now().isoformat(),
        }
        servers_list.append(server_entry)

    def add_server(self, guild: discord.Guild):
        servers = self._read_servers()

        # Check if server already exists
        if any(server["id"] == guild.id for server in servers):
            print(f"Server already in list: {guild.name} (ID: {guild.id})")
            return False

        self._add_server_internal(guild, servers)
        self._write_servers(servers)
        print(f"Added to server list: {guild.name} (ID: {guild.id})")
        return True

    def remove_server(self, guild_id: int):
        servers = self._read_servers()
        initial_count = len(servers)
        updated_servers = [s for s in servers if s["id"] != guild_id]

        if len(updated_servers) < initial_count:
            self._write_servers(updated_servers)
            print(f"Removed server from list: {guild_id}")
            return True
        return False

    def get_servers(self) -> list:
        return self._read_servers()

    def get_server(self, guild_id: int) -> dict:
        servers = self._read_servers()
        return next((s for s in servers if s["id"] == guild_id), None)
