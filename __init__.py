from mycroft import MycroftSkill, intent_handler

# Mycroft Colors
blue = "#22A7F0"
blue_dark = "#2C3E50"
blue_pale = "#8CE0FE"
green = "#40DBB0"
orange = "#FD9E66"
yellow = "#FEE255"


class WifiConnect(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        """Create event handlers"""
        self.add_event("mycroft.internet.connected", self.handle_internet_connected)
        self.add_event(
            "system.wifi.setup.hotspot_activated", self.handle_wifi_setup_started
        )
        self.add_event(
            "system.wifi.setup.network_selection",
            self.handle_wifi_setup_network_selection,
        )
        self.add_event("system.wifi.setup.connected", self.handle_wifi_setup_connected)

    @intent_handler("test.intent")
    def show_all_screens(self, message):
        """Show UI screens

        For testing purposes only
        """
        from time import sleep

        images = [
            f"{self.root_dir}/ui/1_connect-to-ap.png",
            f"{self.root_dir}/ui/2_follow-prompt.png",
            f"{self.root_dir}/ui/3_choose-wifi.png",
        ]
        for image in images:
            self.log.info(image)
            self.gui.show_image(image)
            sleep(10)

    def handle_internet_connected(self, message):
        """System came online later after booting."""
        self.enclosure.mouth_reset()

    def handle_wifi_setup_started(self, message):
        """Provide instructions for setting up wifi."""
        text = self.translate("device.wifi.setup.started")
        self.speak_dialog(text)
        image = f"{self.root_dir}/ui/1_connect-to-ap.png"
        self.log.info(image)
        self.gui.show_image(image)

    def handle_wifi_setup_network_selection(self, message):
        """Prompt user to select network and login."""
        text = self.translate("device.wifi.setup.network.selection")
        self.speak_dialog(text)
        self.gui.show_text(text)

    def handle_wifi_setup_connected(self, message):
        """Wifi setup complete, network is connected."""
        self.speak_dialog("device.wifi.setup.complete")
        self.gui["icon"] = "check-circle.svg"
        self.gui["label"] = "Connected"
        self.gui["bgColor"] = green
        self.gui.show_page("status.qml")


def create_skill():
    return WifiConnect()
