from time import sleep
from mycroft import MycroftSkill, intent_handler
from mycroft.audio import wait_while_speaking
from mycroft.messagebus.message import Message
from mycroft.util import connected


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
        # TODO wire up message bus events to trigger prompts.
        # self.add_event("system.wifi.setup.hotspot_activated", self.prompt_to_join_ap)
        # self.add_event(
        #     "system.wifi.setup.hotspot_connected", self.prompt_to_sign_in_to_ap
        # )
        # self.add_event(
        #     "system.wifi.setup.network_selection",
        #     self.prompt_to_select_network,
        # )
        # self.add_event("system.wifi.setup.connected", self.report_setup_complete)

        # TODO Check if connected() just to be safe.
        self.add_event("mycroft.wifi.setup", self.show_all_screens)

    @intent_handler("test.intent")
    def show_all_screens(self, message=None):
        """Show UI screens

        For testing purposes only
        """
        steps = [
            self.prompt_to_join_ap,
            self.prompt_to_sign_in_to_ap,
            self.prompt_to_select_network,
        ]
        for step in steps:
            step()
            wait_while_speaking()
            sleep(5)

        while True:
            if connected():
                self.report_setup_complete()
                break
            else:
                sleep(2)


    def prompt_to_join_ap(self, message=None):
        """Prompt user to join temporary access point."""
        self.speak_dialog("1_ap.created_speech")
        self.gui["phone_image"] = "1_phone_connect-to-ap.png"
        self.gui["prompt"] = "Connect to the \nWifi network"
        self.gui["highlight"] = "MYCROFT"
        self.gui.show_page("prompt.qml", override_idle=True)

    def prompt_to_sign_in_to_ap(self, message=None):
        """Prompt user to sign into access point."""
        self.speak_dialog("2_sign.in.to.ap_speech")
        self.gui["phone_image"] = "2_phone_follow-prompt.png"
        self.gui["prompt"] = "Follow the \nprompt on your \nmobile device or \ncomputer"
        self.gui["highlight"] = ""

    def prompt_to_select_network(self, message=None):
        """Prompt user to select network and login."""
        self.gui["phone_image"] = "3_phone_choose-wifi.png"
        self.gui["prompt"] = "Choose the \nWifi network to \nconnect your \nMycroft device"
        self.gui["highlight"] = ""

    def report_setup_complete(self, message=None):
        """Report when wifi setup is complete, network is connected."""
        self.speak_dialog("4_internet.connected_speech")
        self.gui["bgColor"] = green
        self.gui["icon"] = "check-circle.svg"
        self.gui["label"] = self.translate("4_internet.connected_screen")
        self.gui.remove_page("prompt.qml")
        self.gui.show_page("status.qml")
        wait_while_speaking()
        sleep(5)
        self.gui.release()
        self.bus.emit(Message('mycroft.ready'))

    def report_error(self, message=None):
        """Report if an error occured during wifi setup."""
        self.gui.remove_page("prompt.qml")
        self.gui["bgColor"] = red
        self.gui["icon"] = "times-circle.svg"
        self.gui["label"] = "Incorrect password"
        self.gui.show_page("status.qml")


def create_skill():
    return WifiConnect()
