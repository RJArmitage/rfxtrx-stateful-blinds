CONF_STATE_SUPPORT = "state_support"
CONF_CLOSE_SECONDS = "close_seconds"
CONF_OPEN_SECONDS = "open_seconds"
CONF_SYNC_SECONDS = "sync_seconds"
CONF_CUSTOM_ICON = "custom_icon"
CONF_COLOUR_ICON = "colour_icon"
CONF_PARTIAL_CLOSED = "partial_closed"
CONF_SIGNAL_REPETITIONS_DELAY_MS = "signal_repetition_delay"
CONF_SIGNAL_REPETITIONS = "signal_repetitions"
CONF_ROLLER_MID_ON_CLOSE = "roller_mid_on_close"

CONF_SUPPORTS_MID = "midpoint_supported"
CONF_STEPS_MID = "midpoint_steps"
CONF_SYNC_MID = "midpoint_sync"

CONF_TILT_POS1_MS = "tilt1_ms"
CONF_TILT_POS2_MS = "tilt2_ms"

DEF_STATE_SUPPORT = True
DEF_CLOSE_SECONDS = 30
DEF_OPEN_SECONDS = 30
DEF_SYNC_SECONDS = 2
DEF_SUPPORTS_MID = False
DEF_STEPS_MID = 10
DEF_SYNC_MID = False
DEF_CUSTOM_ICON = True
DEF_COLOUR_ICON = True
DEF_PARTIAL_CLOSED = True
DEF_SIGNAL_REPETITIONS_DELAY_MS = 250
DEF_SIGNAL_REPETITIONS = 1
DEF_ROLLER_MID_ON_CLOSE = True

DEF_TILT_POS1_MS = 1750
DEF_TILT_POS2_MS = 1750

DEVICE_PACKET_TYPE_BLINDS1 = 0x19
DEVICE_PACKET_SUBTYPE_BLINDST19 = 0x13
DEVICE_PACKET_TYPE_RFY = 0x1a

DEVICE_TYPE_VOGUE_VERTICAL = "VogueVert"

SVC_UPDATE_POSITION = "update_cover_position"
SVC_INCREASE_TILT = "increase_cover_tilt"
SVC_DECREASE_TILT = "decrease_cover_tilt"
SVC_SET_MOVEMENT_ALLOWED = "set_movement_allowed"

ATTR_AUTO_REPEAT = "repeat_automatically"
ATTR_MOVEMENT_ALLOWED = "allowed"

# These SUPPORT_* constants are deprecated as of Home Assistant 2022.5.
# Please use the CoverEntityFeature enum instead.
SUPPORT_OPEN = 1
SUPPORT_CLOSE = 2
SUPPORT_SET_POSITION = 4
SUPPORT_STOP = 8
SUPPORT_OPEN_TILT = 16
SUPPORT_CLOSE_TILT = 32
SUPPORT_STOP_TILT = 64
SUPPORT_SET_TILT_POSITION = 128

CONF_VENETIAN_BLIND_MODE = "venetian_blind_mode"
CONST_VENETIAN_BLIND_MODE_DEFAULT = "Unknown"
CONST_VENETIAN_BLIND_MODE_EU = "EU"
CONST_VENETIAN_BLIND_MODE_US = "US"
