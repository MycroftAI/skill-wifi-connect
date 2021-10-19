# Copyright 2020 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Mycroft skill for joining a device to a WiFi network."""
from time import sleep

from mycroft.audio import stop_speaking, wait_while_speaking
from mycroft.identity import IdentityManager
from mycroft.messagebus import Message
from mycroft.skills import MycroftSkill, intent_handler
from mycroft.util import connected


MARK_II = 'mycroft_mark_2'

def has_paired_before() -> bool:
    """Simple check for whether a device has previously been paired.

    This does not verify that the pairing information is valid or up to date.
    The assumption being - if it's previously paired, then it has previously
    connected to the internet.
    """
    identity = IdentityManager.get()
    return identity.uuid != ""

class WifiConnect(MycroftSkill):
    """Skill that joins a device to a WiFi network.

    Attributes:
        page_showing: on a GUI enabled device, the page being displayed
    """
    def __init__(self):
        super().__init__()
        self.page_showing = None

    @property
    def platform(self):
        return self.config_core['enclosure'].get('platform', 'unknown')

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
        if has_paired_before():
            self.log.debug(
                "Device has previously connected to a network. Delaying Wifi "
                "to provide system time to connect to slower Wifi networks."
            )
            sleep(25)
        else:
            # Give the GUI and Wifi Connect time to get started.
            sleep(5)
        if not connected():
            self.show_all_screens()

    @intent_handler("test.intent")
    def show_all_screens(self, _):
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

    def prompt_to_join_ap(self):
        """Prompt user to join temporary access point."""
        self.speak_dialog("1_ap.created_speech")
        self._show_page("access_point_select")

    def prompt_to_sign_in_to_ap(self):
        """Prompt user to sign into access point."""
        self._show_page("follow_prompt")
        self.speak_dialog("2a_sign.in.to.ap_speech", wait=True)
        self.speak_dialog("2b_sign.in.to.ap_speech")

    def prompt_to_select_network(self):
        """Prompt user to select network and login."""
        self._show_page("network_select")

    def check_connection(self):
        """Determine if the device connected successfully."""
        is_connected = connected()
        if is_connected:
            stop_speaking()
            self.report_setup_complete()
        return is_connected

    def report_setup_complete(self):
        """Report when wifi setup is complete, network is connected."""
        self.gui["label"] = self.translate("4_internet.connected_screen")
        self.gui.show_page("wifi_success_scalable.qml")
        sleep(5)
        self.gui.release()
        self.bus.emit(Message('mycroft.ready'))

    def _show_page(self, page_name_prefix: str):
        """Shows the appropriate screen for the device's platform.

        Args:
            page_name_prefix: part of the page name not platform-specific
        """
        if self.gui.connected:
            if self.platform == MARK_II:
                page_name_suffix = "_mark_ii"
            else:
                page_name_suffix = "_scalable"
            page_name = page_name_prefix + page_name_suffix + ".qml"
            if self.page_showing is not None:
                self.gui.remove_page(self.page_showing)
            self.gui.show_page(page_name, override_idle=True)
            self.page_showing = page_name


def create_skill():
    return WifiConnect()
