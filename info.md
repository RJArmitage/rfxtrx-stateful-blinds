Replaces the built-in integration for RFXtrx covers to add "state" to the basic capabilities. This is only available for blinds that support it. All other RFXtrx operations fall back on the in-built support from Home Assistant.

State? Mainly applicable to tilting blinds. The idea is that Home Assistant will know how much tilt the blind has so that it knows how much extra tilt to apply to get the requested result. So, if the blind is currently 20% tilted and we want 70% tilt, the component knows to apply 50% more tilt to what it already has.
