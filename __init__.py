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
from enum import Enum
from time import sleep

from mycroft.audio import stop_speaking
from mycroft.identity import IdentityManager
from mycroft.messagebus import Message
from mycroft.skills import MycroftSkill, intent_handler


MARK_II = "mycroft_mark_2"


class State(str, Enum):
    """State of the wifi-connect skill"""

    IDLE = "idle"
    ACTIVATING_HOTSPOT = "activating-hotspot"
    WAITING_FOR_PASSWORD = "waiting-for-password"
    CONNECTING_TO_WIFI = "connecting-to-wifi"


class WifiConnect(MycroftSkill):
    """Skill that joins a device to a WiFi network.

    Attributes:
        page_showing: on a GUI enabled device, the page being displayed
    """

    def __init__(self):
        super().__init__()
        self.page_showing = None

        self.state: State = State.IDLE

    @property
    def platform(self):
        return self.config_core["enclosure"].get("platform", "unknown")

    def initialize(self):
        """Create event handlers"""

        # Trigger condition for skill
        self.add_event(
            "hardware.network-not-detected", self._handle_network_not_detected
        )

        self.add_event("system.wifi.setup.started", self._handle_started)

        # Hotspot has been created
        self.add_event(
            "system.wifi.setup.hotspot-activated",
            self._handle_hotspot_activated,
        )

        # User has connected to portal page
        self.add_event(
            "system.wifi.setup.hotspot-connected",
            self._handle_hotspot_connected,
        )

        # User has selected an access point
        self.add_event(
            "system.wifi.setup.hotspot-selected",
            self._handle_hotspot_selected,
        )

        # Hotspot removed so wifi connection can be attempted
        self.add_event(
            "system.wifi.setup.hotspot-deactivated",
            self._handle_hotspot_deactivated,
        )

        # Error condition
        self.add_event("system.wifi.setup.failed", self._handle_setup_failed)

        # Success condition for skill
        self.add_event(
            "hardware.network-detected", self._handle_network_detected
        )

        # Setup is complete
        self.add_event(
            "system.wifi.setup.connected", self._handle_setup_connected
        )

    # -------------------------------------------------------------------------

    def _handle_network_not_detected(self, _message=None):
        if self.state == State.IDLE:
            # First run of the skill
            self.bus.emit(Message("system.wifi.setup.started"))
        elif self.state == State.CONNECTING_TO_WIFI:
            # WiFi connection attempt failed
            self.bus.emit(Message("system.wifi.setup.failed"))

    def _handle_started(self, _message=None):
        if self.state == State.IDLE:
            self.state = State.ACTIVATING_HOTSPOT
            self.bus.emit(Message("system.wifi.setup.create-hotspot"))

    def _handle_hotspot_activated(self, _message=None):
        if self.state == State.ACTIVATING_HOTSPOT:
            self.state = State.WAITING_FOR_PASSWORD
            self._prompt_to_select_access_point()
            self._display_select_wifi_network()

    def _handle_hotspot_selected(self, _message=None):
        if self.state == State.WAITING_FOR_PASSWORD:
            self.state = State.CONNECTING_TO_WIFI

            # Inform user that connection is being attempted
            self._show_connecting_page()

    def _handle_hotspot_deactivated(self, _message=None):
        if self.state == State.CONNECTING_TO_WIFI:
            # Request network detection from enclosure
            self.bus.emit(Message("hardware.detect-network"))

    def _handle_hotspot_connected(self, _message=None):
        if self.state == State.WAITING_FOR_PASSWORD:
            self._prompt_to_select_wifi_network()

    def _handle_setup_failed(self, _message=None):
        self.log.info("Wi-Fi setup failed")

        if self.state == State.CONNECTING_TO_WIFI:
            self.state = State.IDLE
            self._show_failure_page()

            # Start over
            self.bus.emit(Message("system.wifi.setup.started"))

    def _handle_network_detected(self, _message=None):
        if self.state == State.CONNECTING_TO_WIFI:
            # WiFi setup succeeded
            self.bus.emit(Message("system.wifi.setup.connected"))

    def _handle_setup_connected(self, _message=None):
        self.log.info("Wi-Fi setup succeeded")

        self.state = State.IDLE
        self.bus.emit(Message("system.wifi.setup.ended"))

        self._report_setup_complete()

    # -------------------------------------------------------------------------

    def _prompt_to_select_access_point(self):
        """Prompt user to join temporary access point."""
        self._show_page("access_point_select")
        self.speak_dialog("access-point-created", wait=True)

    def _prompt_to_select_wifi_network(self):
        """Prompt user to sign into access point."""
        self._show_page("follow_prompt")
        self.speak_dialog("choose-wifi-network", wait=True)
        self.speak_dialog("no-prompt", wait=True)

    def _display_select_wifi_network(self):
        """Prompt user to select network and login."""
        self._show_page("network_select")

    def _show_connecting_page(self, _message=None):
        """Inform user that wifi connection is being attempted"""
        self._show_page("connecting")

    def _show_failure_page(self, _message=None):
        """Inform user that wifi connection failed"""
        self._show_page("wifi_failure")
        self.speak_dialog("wifi-failure", wait=True)

    def _report_setup_complete(self):
        """Report when wifi setup is complete, network is connected."""
        self.gui["label"] = self.translate("connected")
        self._show_page("wifi_success")
        sleep(5)
        self.gui.release()

    # -------------------------------------------------------------------------

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
