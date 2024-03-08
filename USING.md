# How to Use

Simply add blinds using the standard RFXtrx integration options dialog as you would have done before. The component will automatically detect if you select a supported blind type. The dialog will then show some additional options:

## Somfy Venetian Blinds

These options are only available when the venetian blind mode is set to "`US`" or "`EU`". Note that Somfy venetian blinds have a "`my`" position which would normally be set to the blind mid position (ie. fully tilted open). Hence a Somfy venetian blind has three directly supported states - fully lifted, fully closed and tilted open.

At the moment the component does not support the full tilt operations that the motor is capable of. Instead, it supports tilting to the mid point (50%) along with an extra tilt before and after this point (25% and 75%). The extra positions are provided by tilting up or down from the mid point for a number of milliseconds. Set whatever works for you in the configuration.

- **Number of signal repetitions** - How many times should each request message be sent to the motor. As we have no way of knowing if the motor has received the message then increasing this can help. However, repeating a Somfy request can have unexpected results so it's best to leave set to "1".
- **Venetian blind mode** - According the RFXtrx documentation, Somfy motors can be in either US or European mode. In practice I live in Europe but find that I need "US" mode so I'm not sure this is helpful. If set to "Unknown" then the blind is assumed not to support tilt operations.
- **Provide stateful support** - If set then the stateful component is used. If clear then the default RFXtrx support is sused for this blind.
- **Open time (secs)** - Number of seconds that the blind requires to completely lift. Allow the time for the worst case which would be to lift from fully tilted upward.
- **Close time (secs)** - Number of seconds that the blind requires to completely close when fully lifted.
- **Mid open/close time (ms)** - Number of milliseconds that the blind requires to tilt to its mid point (the "my" position). Allow the time for the worst case which would be to tilt to the mid position from fully tilted upward as the blind will normally first tilt to closed and then tilt to the mid point. For a roller blind this is the time (in milliseconds) to close the blind to its mid position.
- **Lower tilt time from midpoint (ms)** - The component simulates a 25% tilt operation by tilting to the mid point and then closing the blind for this number of milliseconds. This is not ideal and will be removed if better tilt support is added to RFXtrx.
- **Upper tilt time from midpoint (ms)** - The component simulates a 75% tilt operation by tilting to the mid point and then lifting the blind for this number of milliseconds. Again this will be removed if better tilt support is added to RFXtrx.
- **Custom cover icon** - Select to use an icon showing the state of the cover.
- **Highlight open cover** - Select to show open covers using a highlight colour. In this case "open" means a cover where it is likely to be possible to see through from outside.

At present a tilting blind is able to provide three open tilt positions. The Somfy motor can do better than this and if better support is added to RFXtrx then the component will provide it.

Note that the open, close and mid times are important as a Somfy motor reacts differently to a "`stop`" command if the blind is in motion or stationary. The component will only accept the "`stop`" command if it believes the blind is in motion. The mid time is important as the component needs to know how long to allow the blind to reach the mid position before it then tries to tilt to another position. This makes the tilt operation more reliable. If in doubt allow more time. This will have no impact other than to make operations a little slower. See what works for you.

The Somfy tilting blind will not lift the blind if instructed to open. Instead it will use the tilt to mid operation to tilt the blind open. Similarly a close command will tilt to closed. This also takes into account if the blind is currently lifted. So, an open or close instruction will always protect privacy by ensuring the blind is tilted as necessary. To lift the blind set the cover position to more than 50% using the "`cover.set_cover_position`" service call or just use the position slider in Lovelace. Using Alexa you can lift the blind using something like "`Alexa, set office blind to 100%`"

## Somfy Roller Blinds

These options are only available when the venetian blind mode is set to "`Unknown`" or "`EU`". Note that Somfy venetian blinds have a "`my`" position which would normally be set to the blind mid position (ie. fully tilted open). Hence a Somfy venetian roller has three directly supported states - fully lifted, fully closed and mid position open.

At the moment the component does not support the full tilt operations that the motor is capable of. Instead, it supports tilting to the mid point (50%) along with an extra tilt before and after this point (25% and 75%). The extra positions are provided by tilting up or down from the mid point for a number of milliseconds. Set whatever works for you in the configuration.

- **Number of signal repetitions** - How many times should each request message be sent to the motor. As we have no way of knowing if the motor has received the message then increasing this can help. However, repeating a Somfy request can have unexpected results so it's best to leave set to "1".
- **Venetian blind mode** - Set to "Unknown" for a roller blind.
- **Provide stateful support** - If set then the stateful component is used. If clear then the default RFXtrx support is sused for this blind.
- **Open time (secs)** - Number of seconds that the blind requires to completely lift. Allow the time for the worst case which would be to lift from fully tilted upward.
- **Close time (secs)** - Number of seconds that the blind requires to completely close when fully lifted. _This apples to both tilt and roller blinds._
- **Mid open/close time (ms)** - Number of milliseconds that the blind requires to open or close to its "my" position.
- **Custom cover icon** - Select to use an icon showing the state of the cover.
- **Highlight open cover** - Select to show open covers using a highlight colour. In this case "open" means a cover where it is likely to be possible to see through from outside. The "my" position is assumed to be "open".

Note that the open, close and mid times are important as a Somfy motor reacts differently to a "`stop`" command if the blind is in motion or stationary. The component will only accept the "`stop`" command if it believes the blind is in motion. If in doubt allow more time. This will have no impact other than to make operations a little slower. See what works for you.

## Lovolite Vogue Vertical Blinds

The Louvolite Vogue vertical blinds motor allows the blinds to be tilted to 0, 45, 90, 135 and 180 degrees. These are positions 0%, 25%, 50%, 75% and 100%. 0% and 100% are both fully closed. 50% is fully open. Closing the blind will tilt to 0%. Opening the blind tilts to 50%.

- **Open time (secs)** - Number of seconds that the blind requires to completely open to 50%. Allow the time for the worst case which would be that the blind starts fully closed.
- **Close time (secs)** - Number of seconds that the blind requires to completely close. Allow the time for the worst case which would be that the blind is tilted to the opposite close position.
- **Custom cover icon** - Select to use an icon showing the state of the cover.
- **Highlight open cover** - Select to show open covers using a highlight colour. In this case "open" means a cover where it is likely to be possible to see through from outside.

## Service Operations

The component adds a new scripting operation:

- **`RFXtrx.update_cover_position`** - Sets the internal state of the position and tilt position of the blind.<br/><br/>This is intended to be used when defining a Somfy group device. In that case the tilt states of any blinds in the Somfy group would be wrong. To solve this simply create an automation to update the states of the individual blinds in the group when the group device changes. For example this automation updates the 5 individual blinds that make up Somfy group "`cover.living_room`" whenever the group tilt position changes:

```
    - alias: "Living Room sync blind state"
      description: "Sync the tilt of individual blinds with group blind"
      trigger:
      - platform: state
        entity_id: cover.living_room
      action:
      - service: RFXtrx.update_cover_position
        data:
          position: '{{ state_attr("cover.living_room", "current_position") }}'
          tilt_position: '{{ state_attr("cover.living_room", "current_tilt_position") }}'
          state: '{{ states("cover.living_room" }}'
        target:
          entity_id:
          - cover.living_room_1
          - cover.living_room_2
          - cover.living_room_3
          - cover.living_room_4
          - cover.living_room_5
      mode: single
```

---

### [<<< Back to README <<<](./README.md)
