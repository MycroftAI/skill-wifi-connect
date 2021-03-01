from time import sleep
from mycroft import MycroftSkill, intent_handler
from mycroft.audio import stop_speaking, wait_while_speaking
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

        # TODO when on screen setup ready - trigger from button push
        # self.add_event("mycroft.wifi.setup", self.show_all_screens)
        sleep(5)
        if not connected():
            self.show_all_screens()

    @intent_handler("test.intent")
    def show_all_screens(self, _=None):
        """Show UI screens at a consistent interval."""
        steps = [
            self.prompt_to_join_ap,
            self.prompt_to_sign_in_to_ap,
            self.prompt_to_select_network,
        ]
        for step in steps:
            if connected():
                break
            step()
            for sec in range(8):
                if self.check_connection():
                    return
                else:
                    sleep(1)
            wait_while_speaking()


        while True:
            if self.check_connection():
                return
            else:
                sleep(2)


    def prompt_to_join_ap(self, _=None):
        """Prompt user to join temporary access point."""
        self.speak_dialog("1_ap.created_speech")
        self.gui["phone_image1"] = "1_phone_connect-to-ap.png"
        self.gui["prompt1"] = "Connect to the \nWifi network"
        self.gui["highlight1"] = "Mycroft"
        self.gui.show_page("prompt1.qml", override_idle=True)

    def prompt_to_sign_in_to_ap(self, _=None):
        """Prompt user to sign into access point."""
        self.speak_dialog("2a_sign.in.to.ap_speech")
        self.gui["phone_image2"] = "2_phone_follow-prompt.png"
        self.gui["prompt2"] = "Follow the \nprompt on your \nmobile device or \ncomputer"
        self.gui.show_page("prompt2.qml")
        wait_while_speaking()
        self.speak_dialog("2b_sign.in.to.ap_speech")
        self.gui["prompt2"] = "If you don't get \na prompt, go to \nstart.mycroft.ai"
        self.gui["phone_image2"] = "3_phone_choose-wifi.png"

    def prompt_to_select_network(self, _=None):
        """Prompt user to select network and login."""
        self.gui["phone_image3"] = "3_phone_choose-wifi.png"
        self.gui["prompt3"] = "Choose the \nWifi network to \nconnect your \nMycroft device"
        self.gui.show_page("prompt3.qml")

    def check_connection(self):
        is_connected = connected()
        if is_connected:
            stop_speaking()
            self.report_setup_complete()
        return is_connected

    def report_setup_complete(self, _=None):
        """Report when wifi setup is complete, network is connected."""
        # self.speak_dialog("4_internet.connected_speech")
        self.gui["bgColor"] = green
        self.gui["icon"] = "check-circle.svg"
        self.gui["label"] = self.translate("4_internet.connected_screen")
        self.gui.remove_page("prompt1.qml")
        self.gui.remove_page("prompt2.qml")
        self.gui.remove_page("prompt3.qml")
        self.gui.show_page("status.qml")
        # wait_while_speaking()
        sleep(5)
        self.gui.release()
        self.bus.emit(Message('mycroft.ready'))

    def report_error(self, _=None):
        """Report if an error occured during wifi setup."""
        self.gui.remove_page("prompt.qml")
        self.gui["bgColor"] = red
        self.gui["icon"] = "times-circle.svg"
        self.gui["label"] = "Incorrect password"
        self.gui.show_page("status.qml")


def create_skill():
    return WifiConnect()
