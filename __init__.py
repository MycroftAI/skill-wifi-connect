from mycroft import MycroftSkill, intent_handler


# Mycroft Colors
blue = "#22A7F0"
blue_dark = "#2C3E50"
blue_pale = "#8CE0FE"
green = "#40DBB0"
yellow = "#FEE255"
orange = "#FD9E66"
red = "#D81159"


class WifiConnect(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        """Create event handlers"""
        self.add_event("mycroft.internet.connected", self.report_setup_complete)
        self.add_event("system.wifi.setup.hotspot_activated", self.prompt_to_join_ap)
        self.add_event(
            "system.wifi.setup.hotspot_connected", self.prompt_to_sign_in_to_ap
        )
        self.add_event(
            "system.wifi.setup.network_selection",
            self.prompt_to_select_network,
        )
        self.add_event("system.wifi.setup.connected", self.report_setup_complete)

    @intent_handler("test.intent")
    def show_all_screens(self, message):
        """Show UI screens

        For testing purposes only
        """
        from time import sleep

        # images = [
        #     f"{self.root_dir}/ui/0_start.png",
        #     f"{self.root_dir}/ui/1_connect-to-ap.png",
        #     f"{self.root_dir}/ui/2_follow-prompt.png",
        #     f"{self.root_dir}/ui/3_choose-wifi.png",
        # ]
        # for image in images:
        #     self.log.info(image)
        #     self.gui.show_image(image)
        #     sleep(10)
        steps = [
            self.prompt_to_join_ap,
            self.prompt_to_sign_in_to_ap,
            self.prompt_to_select_network,
            self.report_setup_complete
        ]
        for step in steps:
            step(None)
            sleep(5)


    def prompt_to_join_ap(self, message):
        """Provide instructions for setting up wifi."""
        text = self.translate("device.wifi.setup.started")
        self.speak_dialog(text)
        self.gui["phone_image"] = "1_phone_connect-to-ap.png"
        self.gui["prompt"] = "Connect to the \nWifi network"
        self.gui["highlight"] = "MYCROFT"
        self.gui.show_page("prompt.qml")

    def prompt_to_sign_in_to_ap(self, message):
        """Provide instructions for setting up wifi."""
        text = self.translate("device.wifi.setup.started")
        self.speak_dialog(text)
        self.gui["phone_image"] = "2_phone_follow-prompt.png"
        self.gui["prompt"] = "Follow the \nprompt on your \nmobile device or \ncomputer"
        self.gui["highlight"] = ""

    def prompt_to_select_network(self, message):
        """Prompt user to select network and login."""
        text = self.translate("device.wifi.setup.network.selection")
        self.speak_dialog(text)
        self.gui["phone_image"] = "3_phone_choose-wifi.png"
        self.gui["prompt"] = "Choose the \nWifi network to \nconnect your \nMycroft device"
        self.gui["highlight"] = ""

    def report_setup_complete(self, message):
        """Wifi setup complete, network is connected."""
        self.speak_dialog("device.wifi.setup.complete")
        self.gui["icon"] = "check-circle.svg"
        self.gui["label"] = "Connected"
        self.gui["bgColor"] = green
        self.gui.remove_page("prompt.qml")
        self.gui.show_page("status.qml")


def create_skill():
    return WifiConnect()
