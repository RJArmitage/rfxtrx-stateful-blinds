import logging
from homeassistant.components.rfxtrx.cover import *
from .ext.cover import async_setup_entry as new_async_setup_entry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    config_entry,
    async_add_entities,
):
    """Set up config entry."""
    _LOGGER.info("Called overridden async_setup_entry")
    await new_async_setup_entry(hass, config_entry, async_add_entities)
