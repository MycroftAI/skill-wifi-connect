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

from mycroft.audio import stop_speaking
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
        self.connected_to_internet = False

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
            self.connect_to_wifi()

    @intent_handler("test-gui.intent")
    def test_gui(self, _):
        """Show GUI screens at a consistent interval.

        Testing wifi setup is difficult because the device must be in a certain state
        for this skill to activate.  This method allows a developer to test changes to
        the GUI without the difficulty of getting the device in a wifi setup state.
        """
        pages = [
            "access_point_select", "follow_prompt", "network_select", "wifi_success"
        ]
        for page in pages:
            self._show_page(page)
            sleep(10)

    def connect_to_wifi(self):
        """Connect the device to a wifi network.

        Mycroft devices need an internet connection for various purposes, such as
        communicating with Selene.  If a device is already connected to the internet,
        this setup logic should be skipped.
        """
        step_timeout = 8
        self.schedule_repeating_event(
            self._check_for_internet_connection,
            when=None,
            frequency=2,
            name="InternetConnectCheck"
        )
        steps = [
            self._prompt_to_select_access_point,
            self._prompt_to_select_wifi_network,
            self._display_select_wifi_network,
        ]
        for step in steps:
            if self.connected_to_internet:
                break
            step()
            sleep_duration = 0
            while not self.connected_to_internet and sleep_duration < step_timeout:
                sleep(1)
                sleep_duration += 1

        while not self.connected_to_internet:
            self.log.debug("No internet connection detected, waiting...")
            sleep(2)

        self.cancel_scheduled_event("InternetConnectCheck")
        self._report_setup_complete()

    def _prompt_to_select_access_point(self):
        """Prompt user to join temporary access point."""
        self._show_page("access_point_select")
        self.speak_dialog("access_point_created", wait=True)

    def _prompt_to_select_wifi_network(self):
        """Prompt user to sign into access point."""
        self._show_page("follow_prompt")
        self.speak_dialog("choose-wifi-network", wait=True)
        self.speak_dialog("no-prompt", wait=True)

    def _display_select_wifi_network(self):
        """Prompt user to select network and login."""
        self._show_page("network_select")

    def _check_for_internet_connection(self):
        """Determine if the device connected successfully."""
        self.connected_to_internet = connected()
        if self.connected_to_internet:
            stop_speaking()

    def _report_setup_complete(self):
        """Report when wifi setup is complete, network is connected."""
        self.gui["label"] = self.translate("connected")
        self._show_page("wifi_success")
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
