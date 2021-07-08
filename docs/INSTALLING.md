# Installing and uninstalling

Simply copy the contents of the "`custom_components/rfxtrx`" folder from gitlab to the "`config/custom_components/rfxtrx`" folder of your Home Assistant system and then restart. If you don't already use the rfxtrx integration then you should add it from the Home Assistant "Integrations" page as usual. If you want to get rid of the new component then simply delete the "`config/custom_components/rfxtrx`" folder and restart Home Assistant.

If you want to use the inbuilt icons then you'll need to do a little more work. Create a folder "`config/www/rfxtrx`" and then copy the contents of the "`custom_components/rfxtrx/www`" folder. So you'll end up with folders "`config/www/rfxtrx/venetian`" and "`config/www/rfxtrx/vertical`". You'll likely need to restart Home Assistant again.

---

### [<<< Back to README <<<](../README.md)
