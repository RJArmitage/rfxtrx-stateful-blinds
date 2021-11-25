import voluptuous as vol
import logging
from homeassistant.components.rfxtrx.cover import supported as cover_supported
from .const import (
    DEF_CLOSE_SECONDS,
    DEF_OPEN_SECONDS,
    DEF_SYNC_SECONDS,
    DEF_SUPPORTS_MID,
    DEF_STEPS_MID,
    DEF_SYNC_MID,
    DEF_TILT_POS1_MS,
    DEF_TILT_POS2_MS,
    DEF_CUSTOM_ICON,
    DEF_COLOUR_ICON,
    DEF_SIGNAL_REPETITIONS_DELAY_MS,
    CONF_CLOSE_SECONDS,
    CONF_OPEN_SECONDS,
    CONF_SYNC_SECONDS,
    CONF_SUPPORTS_MID,
    CONF_STEPS_MID,
    CONF_SYNC_MID,
    CONF_TILT_POS1_MS,
    CONF_TILT_POS2_MS,
    CONF_CUSTOM_ICON,
    CONF_COLOUR_ICON,
    CONF_SIGNAL_REPETITIONS_DELAY_MS,
    DEVICE_PACKET_TYPE_RFY,
    DEVICE_PACKET_TYPE_BLINDS1,
    DEVICE_PACKET_SUBTYPE_BLINDST19
)

_LOGGER = logging.getLogger(__name__)


def update_device_options(device, user_input):
    device[CONF_SUPPORTS_MID] = user_input.get(
        CONF_SUPPORTS_MID, DEF_SUPPORTS_MID)
    device[CONF_SYNC_MID] = user_input.get(CONF_SYNC_MID, DEF_SYNC_MID)
    device[CONF_STEPS_MID] = user_input.get(CONF_STEPS_MID, DEF_STEPS_MID)
    device[CONF_OPEN_SECONDS] = user_input.get(
        CONF_OPEN_SECONDS, DEF_OPEN_SECONDS)
    device[CONF_CLOSE_SECONDS] = user_input.get(
        CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS)
    device[CONF_SYNC_SECONDS] = user_input.get(
        CONF_SYNC_SECONDS, DEF_SYNC_SECONDS)
    device[CONF_TILT_POS1_MS] = user_input.get(
        CONF_TILT_POS1_MS, DEF_TILT_POS1_MS)
    device[CONF_TILT_POS2_MS] = user_input.get(
        CONF_TILT_POS2_MS, DEF_TILT_POS2_MS)
    device[CONF_CUSTOM_ICON] = user_input.get(
        CONF_CUSTOM_ICON, DEF_CUSTOM_ICON)
    device[CONF_COLOUR_ICON] = user_input.get(
        CONF_COLOUR_ICON, DEF_COLOUR_ICON)
    device[CONF_SIGNAL_REPETITIONS_DELAY_MS] = user_input.get(
        CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS)


def update_data_schema(data_schema, device_object, device_data):
    if (cover_supported(device_object)):
        if device_object.device.packettype == DEVICE_PACKET_TYPE_RFY:
            # Add Somfy RFY venetian tilt options
            data_schema.update(
                {
                    # vol.Optional(
                    #     CONF_SUPPORTS_MID,
                    #     default=device_data.get(
                    #         CONF_SUPPORTS_MID, DEF_SUPPORTS_MID)
                    # ): bool,
                    # vol.Optional(
                    #     CONF_SYNC_MID,
                    #     default=device_data.get(CONF_SYNC_MID, DEF_SYNC_MID),
                    # ): bool,
                    # vol.Optional(
                    #     CONF_STEPS_MID,
                    #     default=device_data.get(CONF_STEPS_MID, DEF_STEPS_MID),
                    # ): int,
                    vol.Optional(
                        CONF_SIGNAL_REPETITIONS_DELAY_MS,
                        default=device_data.get(
                            CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS),
                    ): int,
                    vol.Optional(
                        CONF_OPEN_SECONDS,
                        default=device_data.get(
                            CONF_OPEN_SECONDS, DEF_OPEN_SECONDS),
                    ): int,
                    vol.Optional(
                        CONF_CLOSE_SECONDS,
                        default=device_data.get(
                            CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS),
                    ): int,
                    vol.Optional(
                        CONF_SYNC_SECONDS,
                        default=device_data.get(
                            CONF_SYNC_SECONDS, DEF_SYNC_SECONDS),
                    ): int,
                    vol.Optional(
                        CONF_TILT_POS1_MS,
                        default=device_data.get(
                            CONF_TILT_POS1_MS, DEF_TILT_POS1_MS),
                    ): int,
                    vol.Optional(
                        CONF_TILT_POS2_MS,
                        default=device_data.get(
                            CONF_TILT_POS2_MS, DEF_TILT_POS2_MS),
                    ): int,
                    vol.Optional(
                        CONF_CUSTOM_ICON,
                        default=device_data.get(
                            CONF_CUSTOM_ICON, DEF_CUSTOM_ICON),
                    ): bool,
                    vol.Optional(
                        CONF_COLOUR_ICON,
                        default=device_data.get(
                            CONF_COLOUR_ICON, DEF_COLOUR_ICON),
                    ): bool
                }
            )
        elif device_object.device.packettype == DEVICE_PACKET_TYPE_BLINDS1 and device_object.device.subtype == DEVICE_PACKET_SUBTYPE_BLINDST19:
            # Add Lovolite Vogue vertical tilt options
            data_schema.update(
                {
                    vol.Optional(
                        CONF_SIGNAL_REPETITIONS_DELAY_MS,
                        default=device_data.get(
                            CONF_SIGNAL_REPETITIONS_DELAY_MS, DEF_SIGNAL_REPETITIONS_DELAY_MS),
                    ): int,
                    vol.Optional(
                        CONF_OPEN_SECONDS,
                        default=device_data.get(
                            CONF_OPEN_SECONDS, DEF_OPEN_SECONDS),
                    ): int,
                    vol.Optional(
                        CONF_CLOSE_SECONDS,
                        default=device_data.get(
                            CONF_CLOSE_SECONDS, DEF_CLOSE_SECONDS),
                    ): int,
                    vol.Optional(
                        CONF_CUSTOM_ICON,
                        default=device_data.get(
                            CONF_CUSTOM_ICON, DEF_CUSTOM_ICON),
                    ): bool,
                    vol.Optional(
                        CONF_COLOUR_ICON,
                        default=device_data.get(
                            CONF_COLOUR_ICON, DEF_COLOUR_ICON),
                    ): bool
                }
            )
