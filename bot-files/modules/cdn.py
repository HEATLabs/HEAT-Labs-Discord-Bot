from __future__ import annotations
from typing import Any
import aiohttp
from modules.logger import get_logger

logger = get_logger()


# CDN MAPPING INDEX
CDN_TO_GITHUB: dict[str, str] = {
    "https://cdn0.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Static/refs/heads/main/"
    ),
    "https://cdn1.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Configs/refs/heads/main/"
    ),
    "https://cdn2.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Database/refs/heads/main/"
    ),
    "https://cdn5.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Images/refs/heads/main/"
    ),
    "https://cdn7.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Images-Tanks/refs/heads/main/"
    ),
    "https://cdn8.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Images-Maps/refs/heads/main/"
    ),
    "https://cdn13.heatlabs.net/": (
        "https://raw.githubusercontent.com/HEATLabs/HEAT-Labs-Images-Tournaments/refs/heads/main/"
    ),
}


# Convert a HEAT Labs CDN URL to its raw GitHub equivalent.
def convert_cdn_url(url: Any) -> Any:
    if not isinstance(url, str) or not url:
        return url

    url = url.strip()

    for cdn_base, github_base in CDN_TO_GITHUB.items():
        if url.startswith(cdn_base):
            converted = github_base + url[len(cdn_base) :]
            logger.info(f"CDN redirect: {url} -> {converted}")
            return converted

    return url


def is_cdn_url(url: Any) -> bool:
    return isinstance(url, str) and any(
        url.strip().startswith(base) for base in CDN_TO_GITHUB
    )


def register_cdn(cdn_base: str, github_base: str) -> None:
    if not cdn_base.endswith("/"):
        cdn_base += "/"
    if not github_base.endswith("/"):
        github_base += "/"
    CDN_TO_GITHUB[cdn_base] = github_base
    logger.info(f"Registered CDN mapping: {cdn_base} -> {github_base}")


# GLOBAL MONKEY-PATCH
_PATCHED = False


def _patch_aiohttp() -> None:
    global _PATCHED
    if _PATCHED:
        logger.info("aiohttp already patched for CDN conversion — skipping")
        return

    original_request = aiohttp.ClientSession._request
    logger.info(
        f"Patching aiohttp.ClientSession._request "
        f"(orig={original_request}) with {len(CDN_TO_GITHUB)} CDN mappings"
    )

    async def patched_request(self, method, str_or_url, *args, **kwargs):
        if isinstance(str_or_url, str):
            str_or_url = convert_cdn_url(str_or_url)
        else:
            converted = convert_cdn_url(str(str_or_url))
            if converted != str(str_or_url):
                str_or_url = converted
        return await original_request(self, method, str_or_url, *args, **kwargs)

    aiohttp.ClientSession._request = patched_request
    _PATCHED = True
    logger.info("aiohttp patched for global CDN conversion")


# Apply immediately on import.
_patch_aiohttp()
_original_set_image = None
_original_set_thumbnail = None


def _patch_discord_embed() -> None:
    global _original_set_image, _original_set_thumbnail
    import discord

    if _original_set_image is not None:
        return

    _original_set_image = discord.Embed.set_image
    _original_set_thumbnail = discord.Embed.set_thumbnail

    def set_image(self, *, url):
        return _original_set_image(self, url=convert_cdn_url(url))

    def set_thumbnail(self, *, url):
        return _original_set_thumbnail(self, url=convert_cdn_url(url))

    discord.Embed.set_image = set_image
    discord.Embed.set_thumbnail = set_thumbnail
    logger.info("discord.Embed image helpers patched for CDN conversion")


_patch_discord_embed()
