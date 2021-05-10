# coding=utf-8
from __future__ import absolute_import

__author__ = "jneilliii <jneilliii_github@gmail.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2021 jneilliii - Released under terms of the AGPLv3 License"

import octoprint.plugin
import pywemo
import socket


class PSUControl_Wemo(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.RestartNeedingPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.config = dict()

    def get_settings_defaults(self):
        return dict(
            address=''
        )

    def on_settings_initialized(self):
        self.reload_settings()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))

    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def send(self, cmd):
        # try to connect via ip address
        port = None
        plugip = self.config["address"]
        try:
            if ':' in plugip:
                plugip, port = plugip.split(':', 1)
                port = int(port)
            socket.inet_aton(plugip)
        except socket.error or ValueError:
            # try to convert hostname to ip
            try:
                plugip = socket.gethostbyname(plugip)
            except (socket.herror, socket.gaierror):
                return None

        try:
            if port is None:
                port = pywemo.ouimeaux_device.probe_wemo(plugip)
            url = "http://{}:{}/setup.xml".format(plugip, port)
            url = url.replace(':None', '')
            device = pywemo.discovery.device_from_description(url, None)

            if cmd == "info":
                return device.get_state()
            elif cmd == "on":
                device.on()
                return 1
            elif cmd == "off":
                device.off()
                return 0
        except socket.error:
            return None

    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        self.send("on")

    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        self.send("off")

    def get_psu_state(self):
        status = self.send("info")
        return status

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

    def get_settings_version(self):
        return 1

    def on_settings_migrate(self, target, current=None):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(
            psucontrol_wemo=dict(
                displayName="PSU Control - Wemo",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="jneilliii",
                repo="OctoPrint-PSUControl-Wemo",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/jneilliii/OctoPrint-PSUControl-Wemo/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "PSU Control - Wemo"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_Wemo()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
