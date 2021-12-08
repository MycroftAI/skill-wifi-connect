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
import asyncio
import threading
from time import sleep

from mycroft.audio import stop_speaking
from mycroft.identity import IdentityManager
from mycroft.messagebus import Message
from mycroft.skills import MycroftSkill, intent_handler
from mycroft.util.network_utils import (
    get_dbus,
    get_network_manager,
    NM_NAMESPACE,
)


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
            "system.wifi.setup.hotspot_activated",
            self._prompt_to_select_access_point,
        )

        self.add_event(
            "system.wifi.setup.hotspot_connected",
            self._prompt_to_select_wifi_network,
        )

        self.add_event(
            "system.wifi.setup.connected", self._report_setup_complete
        )

        # Start skill logic only if network not connected
        self.add_event("hardware.network-not-detected", self.connect_to_wifi)

    def connect_to_wifi(self):
        """Connect the device to a wifi network.

        Mycroft devices need an internet connection for various purposes, such as
        communicating with Selene.  If a device is already connected to the internet,
        this setup logic should be skipped.
        """
        # Create a separate thread of DBus interaction
        async_thread = threading.Thread(
            target=self._connect_to_wifi_async, daemon=True
        )
        async_thread.start()

    def _connect_to_wifi_async(self):
        """Create new event loop and run DBus code"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._dbus_async())
        loop.close()

    async def _dbus_async(self):
        try:
            self.log.info("Wi-Fi connection process started")
            self.bus.emit(Message("system.wifi.setup.started"))

            dbus = get_dbus()
            await dbus.connect()

            _nm_object, nm_interface = await get_network_manager(dbus)

            (
                wifi_props_interface,
                wifi_wireless_interface,
            ) = await self._get_wireless_device(dbus, nm_interface)

            assert (wifi_props_interface is not None) and (
                wifi_wireless_interface is not None
            ), "No Wi-Fi device found"

            async def is_hotspot_up():
                wifi_mode = await wifi_wireless_interface.get_mode()
                return wifi_mode == NM_802_11_MODE_AP

            # Subscribe to changes in the wifi device properties
            props_changed = asyncio.Event()

            def properties_changed(
                _interface, _changed_props, _invalidated_props
            ):
                props_changed.set()

            wifi_props_interface.on_properties_changed(properties_changed)

            # Wait for hotspot to be active
            self.log.info("Waiting for Mycroft hotspot to activate")
            while not (await is_hotspot_up()):
                await props_changed.wait()

            self.log.info("Mycroft hotspot activated")

            # Mycroft hotspot is active
            self.bus.emit(Message("system.wifi.setup.hotspot_activated"))

            # TODO: Any way to detect connection from client?
            await asyncio.sleep(10)

            # User has connected to hotspot
            self.bus.emit(Message("system.wifi.setup.hotspot_connected"))

            # Now wait for hotspot to go away (user has entered # credentials)
            self.log.info("Waiting for Mycroft hotspot to deactivate")
            props_changed.clear()
            while (await is_hotspot_up()):
                await props_changed.wait()
                props_changed.clear()

            self.log.info("Mycroft hotspot deactivated")

            self.bus.emit(Message("system.wifi.setup.connected"))

            # Clean up
            wifi_props_interface.off_properties_changed(properties_changed)
            await dbus.wait_for_disconnect()
        except Exception as error:
            self.log.exception("error while connecting to wi-fi")
            self.bus.emit(
                Message("system.wifi.setup.error", data={"error": str(error)})
            )

        self.bus.emit(Message("system.wifi.setup.ended"))

    async def _get_wireless_device(self, dbus, nm_interface):
        """Return props/wireless interfaces for first wifi device"""

        # Find the first wi-fi device
        wifi_wireless_interface = None
        wifi_props_interface = None

        for device_path in await nm_interface.get_all_devices():
            dev_introspect = await dbus.introspect(NM_NAMESPACE, device_path)
            dev_object = dbus.get_proxy_object(
                NM_NAMESPACE, device_path, dev_introspect
            )

            dev_interface = dev_object.get_interface(f"{NM_NAMESPACE}.Device")

            dev_type = await dev_interface.get_device_type()

            if dev_type == NM_DEVICE_TYPE_WIFI:
                self.log.debug("Wi-Fi device found: %s", device_path)

                # Get a Device.Wireless interface to get at mode, etc.
                # https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html#NM80211Mode
                wifi_wireless_interface = dev_object.get_interface(
                    f"{NM_NAMESPACE}.Device.Wireless",
                )

                # Get access to PropertiesChanged signal
                wifi_props_interface = dev_object.get_interface(
                    "org.freedesktop.DBus.Properties"
                )
                break

        return wifi_props_interface, wifi_wireless_interface

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
        self.bus.emit(Message("mycroft.ready"))

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
