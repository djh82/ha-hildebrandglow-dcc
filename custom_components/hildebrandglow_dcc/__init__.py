"""The Hildebrand Glow (DCC) integration."""
from __future__ import annotations

import logging
import asyncio
from .glowmarkt import BrightClient, AuthorizationError
import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, ConfigEntryAuthFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hildebrand Glow (DCC) from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Authenticate with the API
    try:
        glowmarkt = await hass.async_add_executor_job(
            BrightClient, entry.data["username"], entry.data["password"]
        )
    except requests.Timeout as ex:
        raise ConfigEntryNotReady(f"Timeout: {ex}") from ex
    except requests.exceptions.ConnectionError as ex:
        raise ConfigEntryNotReady(f"Cannot connect: {ex}") from ex
    except AuthorizationError as ex:
        raise ConfigEntryAuthFailed from ex
    except Exception as ex:  # pylint: disable=broad-except
        raise ConfigEntryNotReady(f"Unexpected exception: {ex}") from ex
    else:
        _LOGGER.debug("Successful Post to %sauth", glowmarkt.url)

    # Set API object
    hass.data[DOMAIN][entry.entry_id] = glowmarkt
    hass.data[DOMAIN] = {"postcode": entry.data.get("postcode")}

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except (asyncio.TimeoutError, TimeoutException) as ex:
        raise ConfigEntryNotReady(
            f"Timeout while loading config entry for {PLATFORMS}"
        ) from ex


    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
