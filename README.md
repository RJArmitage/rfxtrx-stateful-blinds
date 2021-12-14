# What is this?

This component extends the built-in Home Assistant integration for RFXtrx covers. It attempts to add cover "state" to the basic capabilities. This is only available for blinds that support it. All other RFXtrx operations fall back on the in-built support from Home Assistant.

- _State?_ The idea is that a blind has some idea of whether it is up, down, tilted or whatever and by how much.
- _Why is that useful?_ If you only control blinds via a controller then it isn't. You can see the blind and know which button to press on your controller to get what you want. If it's half closed and you wasnt it fully closed then you'll press the button to get what you want. However, if you are using a script then that doesn't work. Also, some blinds - such as my Somfy blinds - react differently to the same controller operation depending upon their state. Again in a script that's no use. A script needs a consistent result to an order.
- _So what does this give me?_ With state in Home Assistant then the component will know how much tilt the blind currently has so that it knows how much extra tilt to apply to get the requested result. So, if the blind is currently 20% tilted and we want 70% tilt, the component knows to apply 50% more tilt to what it already has.

# Why does it exist? Do I need it?

You possibly don't - it's intended to satisfy a specific requirement. Maybe you share it with me...

I have a bunch of venetian blinds which use Somfy motors. Now for me the whole point of venetian blinds is to provide more control over the light in my home while maintaining privacy as best I can. I want some specific capabilities that the base Home Assistant RFXtrx cover support doesn’t give me. Note that this is an opinionated list. These are the facilities that _I_ expect from the way I want to use venetian blinds:

- I want to fully get the benefit of the tilt functions of my blinds. I want to be able to tilt the blind to any position that the blind supports. I have installed venetian blinds to control the light in my house and my privacy. Simply being able to be open or closed doesn't cut it.

- I want to get full scripting support. I should be able to tell the blind to tilt to 70% say and have the blind "know" that it is currently tilted to 30% so needs to step 7 positions to get to 70% tilted. This also makes support via Alexa better as I can tell the blind to tilt to 80% or whatever.

- The concept of "opening" and "closing" the blinds should relate to tilting the blind and not lifting. To me an open venetian blind is one that is dropped and then tilted to open - not one that is lifted. A closed blind is both dropped and tully tilted closed.

- Privacy is key. I want to be certain that the blinds will only attempt to lift if they are explicitly told to. In particular when using Alexa integration, if Alexa is told to "open" the blind then it should do this by tilting the blind to open and not by lifting the blind.

- I want to be able to control my blinds using Somfy groups as well as individually. Somfy motors can assign a single channel on their controller to more than one blind. This means that to control all those blinds only a single instruction is sent. Now, it is possible to do something similar in Home Assistant by creating a cover group. But that's missing the point of the Somfy function. It would mean that each operation would be sent separately to each blind in the group. That's irritating to me as all the blinds start and stop moving separately with a sort of ripple effect. I have 5 blinds in a bay window and this looks untidy! I want to use the function I paid for.

- I want the blind icon in Home Assistant to show the state of the blind. If it's tilted open then that should be obvious and different from it being tilted closed. If the blind is lifted then that should be very obvious.

- I want support for Louvolite Vogue vertical blinds which RFXtrx doesn't normally support.

So, if you have one or more of those requirements then maybe this component will be useful for you. If not then you should continue with the existing built-in Home Assistant RFXtrx integration.

# Which blinds are supported

This implementation only supports two types of blinds. It is fully compatible with everying else that RFXtrx supports and in that case just uses the existing RFXtrx functionality:

- **_Venetian blinds_** using **_Somfy_** battery and mains-powered RTS motors such as **Sonesse** and **Lift & Tilt** motors.

- **_Vertical blinds_** using **_Louvolite Vogue_** battery powered motors. Note that this requires RFXtrx firmware 1044 or better.

- **_Roller blinds_** using **_Somfy_** battery and mains-powered RTS motors.

Why only those blinds? Simply because those are the ones I have so those are the ones I can test against. If you don't have the same devices as me then this likely is't the component to you as you likely wont see any effect.

# Limitations

1. The supported blind motors do not report their state. This means that, for example, if I open a blind in Home Assistant and then close it using the blind's own controller, then Home Assistant won't know and will still show it as open. The component does it's best to synchronise when it can. So if was then later told to close then the blind would remain closed and then be up to date again.

2. At present the full tilt support for Somfy venetian blinds does not work. The RFXtrx documentation says that you can perform a tilt by sending either a 0.5 sec or 2 sec up or down operation depending if you are in EU or US mode. However this simply does not work on my blinds and always either lifts or closes the blind. I suspect the information is out of date for modern motors (my blinds are very new). If better support is added to the RFXtrx firmware then support will be added to this component. This will be great as I'd like to be able to programmatically step to any tilt position. At the moment this component simulates an intermediate tilt position operation. This at least makes the blinds much more useful to me.

---

### [>>> How to Install >>>](docs/INSTALLING.md)

### [>>> How to Use >>>](docs/USING.md)
