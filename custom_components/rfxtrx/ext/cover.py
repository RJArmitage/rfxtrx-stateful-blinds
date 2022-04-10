from __future__ import annotations
import logging
import voluptuous as vol

from homeassistant.helpers import entity_platform
from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION
)

from .const import (
    ATTR_MOVEMENT_ALLOWED,
    CONF_STATE_SUPPORT,
    DEF_STATE_SUPPORT,
    DEVICE_PACKET_TYPE_RFY,
    DEVICE_PACKET_TYPE_BLINDS1,
    DEVICE_PACKET_SUBTYPE_BLINDST19,
    ATTR_AUTO_REPEAT,
    SVC_SET_MOVEMENT_ALLOWED,
    SVC_UPDATE_POSITION,
    SVC_INCREASE_TILT,
    SVC_DECREASE_TILT,
    CONF_VENETIAN_BLIND_MODE,
    CONST_VENETIAN_BLIND_MODE_EU,
    CONST_VENETIAN_BLIND_MODE_US,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION

)

from .louvolite_vogue_blind import LouvoliteVogueBlind
from .somfy_venetian_blind import SomfyVenetianBlind
from .somfy_roller_blind import SomfyRollerBlind

_LOGGER = logging.getLogger(__name__)


def create_cover_entity(device, device_id, entity_info, event=None):
    """Create a cover entitity of any of our supported types"""
    _LOGGER.info("Device ID " + str(device_id))
    _LOGGER.info("Info " + str(entity_info))

    stateSupport = entity_info.get(CONF_STATE_SUPPORT, DEF_STATE_SUPPORT)
    _LOGGER.info("State support  = " + str(stateSupport))

    if stateSupport:
        if int(device_id[0], 16) == DEVICE_PACKET_TYPE_BLINDS1 and int(device_id[1], 16) == DEVICE_PACKET_SUBTYPE_BLINDST19:
            _LOGGER.info(
                "Detected a Louvolite Vogue vertical blind - let's go stateful!")
            return LouvoliteVogueBlind(device, device_id, entity_info)
        elif int(device_id[0], 16) == DEVICE_PACKET_TYPE_RFY:
            venetian_blind_mode = entity_info.get(CONF_VENETIAN_BLIND_MODE)
            if venetian_blind_mode in (CONST_VENETIAN_BLIND_MODE_US, CONST_VENETIAN_BLIND_MODE_EU):
                _LOGGER.info(
                    "Detected a Somfy RFY venetian blind - let's go stateful!")
                return SomfyVenetianBlind(device, device_id, entity_info)
            else:
                _LOGGER.info(
                    "Detected a Somfy RFY roller blind - let's go stateful!")
                return SomfyRollerBlind(device, device_id, entity_info)

    # if stateSupport:
    #     if int(device_id[0], 16) == DEVICE_PACKET_TYPE_BLINDS1 and int(device_id[1], 16) == DEVICE_PACKET_SUBTYPE_BLINDST19:
    #         _LOGGER.info(
    #             "Detected a Louvolite Vogue vertical blind - let's go stateful!")
    #         return LouvoliteVogueBlind(device, device_id, entity_info)
    #     elif int(device_id[0], 16) == DEVICE_PACKET_TYPE_RFY:
    #         venetian_blind_mode = entity_info.get(CONF_VENETIAN_BLIND_MODE)
    #         if venetian_blind_mode in (CONST_VENETIAN_BLIND_MODE_US, CONST_VENETIAN_BLIND_MODE_EU):
    #             _LOGGER.info(
    #                 "Detected a Somfy RFY venetian blind - let's go stateful!")
    #             return SomfyVenetianBlind(device, device_id, entity_info)
    #         else:
    #             _LOGGER.info(
    #                 "Detected a Somfy RFY roller blind - let's go stateful!")
    #             return SomfyRollerBlind(device, device_id, entity_info)

    return None


async def async_define_sync_services():
    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SVC_UPDATE_POSITION,
        {
            vol.Required(ATTR_POSITION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Required(ATTR_TILT_POSITION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            )
        },
        "async_update_cover_position",
        [SUPPORT_SET_POSITION | SUPPORT_SET_TILT_POSITION],
    )

    platform.async_register_entity_service(
        SVC_INCREASE_TILT,
        {
            vol.Optional(ATTR_AUTO_REPEAT, default=False): bool
        },
        "async_increase_cover_tilt",
        [SUPPORT_SET_TILT_POSITION],
    )

    platform.async_register_entity_service(
        SVC_DECREASE_TILT,
        {
            vol.Optional(ATTR_AUTO_REPEAT, default=False): bool
        },
        "async_decrease_cover_tilt",
        [SUPPORT_SET_TILT_POSITION],
    )

    platform.async_register_entity_service(
        SVC_SET_MOVEMENT_ALLOWED,
        {
            vol.Required(ATTR_MOVEMENT_ALLOWED, default=True): bool
        },
        "async_set_movement_allowed",
        [SUPPORT_SET_POSITION | SUPPORT_SET_TILT_POSITION],
    )
