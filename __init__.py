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


MARK_II = "mycroft_mark_2"

# NetworkManager constants
NM_DEVICE_TYPE_WIFI = 2

NM_802_11_MODE_UNKNOWN = 0
NM_802_11_MODE_AP = 3


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
        return self.config_core["enclosure"].get("platform", "unknown")

    def initialize(self):
        """Create event handlers"""

        self.add_event(
            "system.wifi.setup.hotspot-activated",
            self._prompt_to_select_access_point,
        )

        self.add_event(
            "system.wifi.setup.hotspot-connected",
            self._prompt_to_select_wifi_network,
        )

        self.add_event(
            "system.wifi.setup.connected", self._report_setup_complete
        )

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

    def _report_setup_complete(self):
        """Report when wifi setup is complete, network is connected."""
        self.gui["label"] = self.translate("connected")
        self._show_page("wifi_success")
        sleep(5)
        self.gui.release()

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
