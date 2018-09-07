"""
A component which allows you to update your custom cards and components.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_updater
"""

import logging
import os
import subprocess
import time
from datetime import timedelta
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

__version__ = '2.2.1'

_LOGGER = logging.getLogger(__name__)

CONF_TRACK = 'track'
CONF_HIDE_SENSOR = 'hide_sensor'
CONF_SHOW_INSTALLABLE = 'show_installable'
CONF_CARD_CONFIG_URLS = 'card_urls'
CONF_COMPONENT_CONFIG_URLS = 'component_urls'

DOMAIN = 'custom_updater'
CARD_DATA = 'custom_card_data'
COMPONENT_DATA = 'custom_component_data'
INTERVAL = timedelta(days=1)

ATTR_CARD = 'card'
ATTR_COMPONENT = 'component'
ATTR_ELEMENT = 'element'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_TRACK, default=['cards', 'components']):
            vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_HIDE_SENSOR, default=False): cv.boolean,
        vol.Optional(CONF_SHOW_INSTALLABLE, default=False): cv.boolean,
        vol.Optional(CONF_CARD_CONFIG_URLS, default=[]):
            vol.All(cv.ensure_list, [cv.url]),
        vol.Optional(CONF_COMPONENT_CONFIG_URLS, default=[]):
            vol.All(cv.ensure_list, [cv.url]),
    })
}, extra=vol.ALLOW_EXTRA)

DEFAULT_REMOTE_CARD_CONFIG_URL = 'https://raw.githubusercontent.com/custom-cards/information/master/repos.json'
DEFAULT_REMOTE_COMPONENT_CONFIG_URL = 'https://raw.githubusercontent.com/custom-components/information/master/repos.json'


def setup(hass, config):
    """Set up this component."""
    conf_track = config[DOMAIN][CONF_TRACK]
    conf_hide_sensor = config[DOMAIN][CONF_HIDE_SENSOR]
    config_show_installabe = config[DOMAIN][CONF_SHOW_INSTALLABLE]
    conf_card_urls = [DEFAULT_REMOTE_CARD_CONFIG_URL] + config[DOMAIN][CONF_CARD_CONFIG_URLS]
    conf_component_urls = [DEFAULT_REMOTE_COMPONENT_CONFIG_URL] + config[DOMAIN][CONF_COMPONENT_CONFIG_URLS]

    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report'
                 ' them here: https://github.com/custom-components/custom_updater', __version__)

    ha_conf_dir = str(hass.config.path())
    if 'cards' in conf_track:
        card_controller = CustomCards(hass, ha_conf_dir, conf_hide_sensor, conf_card_urls, config_show_installabe)
        track_time_interval(hass, card_controller.cache_versions, INTERVAL)
    if 'components' in conf_track:
        components_controller = CustomComponents(hass, ha_conf_dir, conf_hide_sensor, conf_component_urls, config_show_installabe)
        track_time_interval(hass, components_controller.cache_versions, INTERVAL)

    def check_all_service(call):
        """Set up service for manual trigger."""
        if not conf_track or 'cards' in conf_track:
            card_controller.cache_versions()
        if not conf_track or 'components' in conf_track:
            components_controller.cache_versions()

    def update_all_service(call):
        """Set up service for manual trigger."""
        if not conf_track or 'cards' in conf_track:
            card_controller.update_all()
        if not conf_track or 'components' in conf_track:
            components_controller.update_all()

    def install_service(call):
        """install single component/card"""
        element = call.data.get(ATTR_ELEMENT)
        _LOGGER.debug('Installing %s', element)
        card_controller.install(element)
        components_controller.install(element)

    if not conf_track or 'cards' in conf_track:
        def upgrade_card_service(call):
            """Set up service for manual trigger."""
            card_controller.upgrade_single(call.data.get(ATTR_CARD), 'auto')
        hass.services.register(DOMAIN, 'upgrade_single_card', upgrade_card_service)

    if not conf_track or 'components' in conf_track:
        def upgrade_component_service(call):
            """Set up service for manual trigger."""
            components_controller.upgrade_single(call.data.get(ATTR_COMPONENT))
        hass.services.register(DOMAIN, 'upgrade_single_component', upgrade_component_service)

    hass.services.register(DOMAIN, 'check_all', check_all_service)
    hass.services.register(DOMAIN, 'update_all', update_all_service)
    hass.services.register(DOMAIN, 'install', install_service)
    return True


class CustomCards(object):
    """Custom cards controller."""
    def __init__(self, hass, ha_conf_dir, conf_hide_sensor, conf_card_urls, config_show_installabe):
        self.hass = hass
        self._hide_sensor = conf_hide_sensor
        self._config_show_installabe = config_show_installabe
        self.ha_conf_dir = ha_conf_dir
        self.conf_card_urls = conf_card_urls
        self.cards = None
        self._lovelace_gen = False
        self.hass.data[CARD_DATA] = {}
        self.lovelace_gen_check()
        self.cache_versions()

    def lovelace_gen_check(self):
        """Check if lovelace-gen is in use"""
        conf_file = self.ha_conf_dir + '/ui-lovelace.yaml'
        with open(conf_file, 'r') as local:
            for line in local.readlines():
                if 'generated by lovelace-gen.py' in line:
                    self._lovelace_gen = True
        local.close()
        if self._lovelace_gen and os.path.isdir(self.ha_conf_dir + '/lovelace'):
            _LOGGER.debug('Found evidence of lovelace-gen useage, assuming that is beeing used.')
            self._lovelace_gen = True
        else:
            self._lovelace_gen = False

    def cache_versions(self):
        """Cache"""
        self.cards = self.get_all_remote_info()
        self.hass.data[CARD_DATA] = {}
        if self.cards:
            for name, card in self.cards.items():
                remote_version = card[1]
                local_version = self.get_local_version(card[0])
                if self._config_show_installabe:
                    show = remote_version
                else: 
                    show = local_version
                if show:
                    has_update = (remote_version != False and remote_version != local_version and remote_version != '')
                    not_local = (remote_version != False and not local_version)
                    self.hass.data[CARD_DATA][name] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": card[3],
                        "change_log": card[4],
                    }
                    self.hass.data[CARD_DATA]['domain'] = 'custom_cards'
                    self.hass.data[CARD_DATA]['repo'] = '#'
                    if self._hide_sensor:
                        self.hass.data[CARD_DATA]['hidden'] = True
            self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[CARD_DATA])

    def update_all(self):
        """Update all cards"""
        for name in self.hass.data[CARD_DATA]:
            if name not in ('domain', 'repo', 'hidden'):
                try:
                    if self.hass.data[CARD_DATA][name]['has_update'] and not self.hass.data[CARD_DATA][name]['not_local']:
                        self.upgrade_single(name, 'auto')
                except KeyError:
                    _LOGGER.debug('Skipping upgrade for %s, no update available', name)

    def upgrade_single(self, name, method):
        """Update one components"""
        _LOGGER.debug('Starting upgrade for "%s".', name)
        if name in self.hass.data[CARD_DATA]:
            if self.hass.data[CARD_DATA][name]['has_update']:
                remote_info = self.get_all_remote_info()[name]
                remote_file = remote_info[2]
                if method == 'auto':
                    local_file = self.ha_conf_dir + self.get_card_dir(name) + name + '.js'
                else:
                    if self._lovelace_gen:
                        local_file = self.ha_conf_dir + '/lovelace/' + name + '.js'
                    else:
                        local_file = self.ha_conf_dir + '/www/' + name + '.js'
                test_remote_file = requests.get(remote_file)
                if test_remote_file.status_code == 200:
                    with open(local_file, 'wb') as card_file:
                        card_file.write(test_remote_file.content)
                    card_file.close()
                    self.upgrade_lib(name, method)
                    if method == 'auto':
                        self.update_resource_version(name)
                    _LOGGER.info('Upgrade of %s from version %s to version %s complete',
                                 name, self.hass.data[CARD_DATA][name]['local'],
                                 self.hass.data[CARD_DATA][name]['remote'])
                self.hass.data[CARD_DATA][name]['local'] = self.hass.data[CARD_DATA][name]['remote']
                self.hass.data[CARD_DATA][name]['has_update'] = False
                self.hass.data[CARD_DATA][name]['not_local'] = False
                self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[CARD_DATA])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', name)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid card', name)

    def upgrade_lib(self, name, method):
        """Update one components"""
        _LOGGER.debug('Downloading lib for %s if available', name)
        remote_info = self.get_all_remote_info()[name]
        remote_file = remote_info[2][:-3] + '.lib.js'
        if method == 'auto':
            local_file = self.ha_conf_dir + self.get_card_dir(name) + name + '.lib.js'
        else:
            if self._lovelace_gen:
                local_file = self.ha_conf_dir + '/lovelace/' + name + '.lib.js'
            else:
                local_file = self.ha_conf_dir + '/www/' + name + '.lib.js'
        test_remote_file = requests.get(remote_file)
        if test_remote_file.status_code == 200:
            with open(local_file, 'wb') as card_file:
                card_file.write(test_remote_file.content)
            card_file.close()
            _LOGGER.info('Sucessfully upgraded lib for %s', name)

    def install(self, card):
        """install single card"""
        if card in self.hass.data[CARD_DATA]:
            self.hass.data[CARD_DATA][card]['has_update'] = True
            self.upgrade_single(card, 'manual')
            _LOGGER.info('Sucessfully installed %s, make sure you read the documentation on how to set it up.', card)
            return True
        else:
            return False

    def update_resource_version(self, name):
        """Updating the ui-lovelace file"""
        local_version = self.hass.data[CARD_DATA][name]['local']
        remote_version = self.hass.data[CARD_DATA][name]['remote']
        _LOGGER.debug('Updating configuration for %s', name)
        _LOGGER.debug('Upgrading card in config from version %s to version %s', local_version, remote_version)
        if self._lovelace_gen:
            conf_file = self.ha_conf_dir + '/lovelace/main.yaml'
            sedcmd = 's/' + name + '.js?v=' + str(local_version) + '/' + name + '.js?v=' + str(remote_version) + '/'
        else:
            conf_file = self.ha_conf_dir + '/ui-lovelace.yaml'
            sedcmd = 's/\/' + name + '.js?v=' + str(local_version) + '/\/' + name + '.js?v=' + str(remote_version) + '/'
        subprocess.call(["sed", "-i", "-e", sedcmd, conf_file])

    def get_card_dir(self, name):
        """Get card dir"""
        if self._lovelace_gen:
            conf_file = self.ha_conf_dir + '/lovelace/main.yaml'
        else:
            conf_file = self.ha_conf_dir + '/ui-lovelace.yaml'
        with open(conf_file, 'r') as local:
            for line in local.readlines():
                if self._lovelace_gen:
                    if name + '.js' in line:
                        card_dir = '/lovelace/' + line.split('!resource ')[1].split(name + '.js')[0]
                        _LOGGER.debug('Found path "%s" for card "%s"', card_dir, name)
                        break
                else:
                    if '/' + name + '.js' in line:
                        card_dir = line.split(': ')[1].split(name + '.js')[0].replace("local", "www")
                        _LOGGER.debug('Found path "%s" for card "%s"', card_dir, name)
                        break
        return card_dir

    def get_all_remote_info(self):
        """Return all remote info if any."""
        remote_info = {}
        for url in self.conf_card_urls:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    for name, card in response.json().items():
                        try:
                            card = [
                                name,
                                card['version'],
                                card['remote_location'],
                                card['visit_repo'],
                                card['changelog']
                            ]
                            remote_info[name] = card
                        except KeyError:
                            _LOGGER.debug('Gathering remote info for %s failed...', name)
            except:
                _LOGGER.debug('Could not get remote info for url "%s"', url)
        return remote_info

    def get_local_version(self, name):
        """Return the local version if any."""
        card_config = ''
        if self._lovelace_gen:
            conf_file = self.ha_conf_dir + '/lovelace/main.yaml'
            with open(conf_file, 'r') as local:
                for line in local.readlines():
                    if name + '.js' in line:
                        card_config = line
                        break
            local.close()
        else:
            conf_file = self.ha_conf_dir + '/ui-lovelace.yaml'
            with open(conf_file, 'r') as local:
                for line in local.readlines():
                    if '/' + name + '.js' in line:
                        card_config = line
                        break
            local.close()
        if '=' in card_config:
            local_version = card_config.split('=')[1].split('\n')[0]
            _LOGGER.debug('Local version of %s is %s', name, local_version)
            return local_version
        return False


class CustomComponents(object):
    """Custom components controller."""
    def __init__(self, hass, ha_conf_dir, conf_hide_sensor, conf_component_urls, config_show_installabe):
        self.hass = hass
        self._hide_sensor = conf_hide_sensor
        self._config_show_installabe = config_show_installabe
        self.ha_conf_dir = ha_conf_dir
        self.conf_component_urls = conf_component_urls
        self.components = None
        self.hass.data[COMPONENT_DATA] = {}
        self.cache_versions()

    def cache_versions(self):
        """Cache"""
        self.components = self.get_all_remote_info()
        self.hass.data[COMPONENT_DATA] = {}
        if self.components:
            for name, component in self.components.items():
                remote_version = component[1]
                local_version = self.get_local_version(name, component[2])
                if self._config_show_installabe:
                    show = remote_version
                else: 
                    show = local_version
                if show:
                    has_update = (remote_version != False and remote_version != local_version)
                    not_local = (remote_version != False and not local_version)
                    self.hass.data[COMPONENT_DATA][name] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": component[4],
                        "change_log": component[5],
                    }
                    self.hass.data[COMPONENT_DATA]['domain'] = 'custom_components'
                    self.hass.data[COMPONENT_DATA]['repo'] = '#'
                    if self._hide_sensor:
                        self.hass.data[COMPONENT_DATA]['hidden'] = True
            self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[COMPONENT_DATA])

    def update_all(self):
        """Update all components"""
        for name in self.hass.data[COMPONENT_DATA]:
            if name not in ('domain', 'repo', 'hidden'):
                try:
                    if self.hass.data[COMPONENT_DATA][name]['has_update'] and not self.hass.data[COMPONENT_DATA][name]['not_local']:
                        self.upgrade_single(name)
                except KeyError:
                    _LOGGER.debug('Skipping upgrade for %s, no update available', name)

    def upgrade_single(self, name):
        """Update one components"""
        _LOGGER.debug('Starting upgrade for "%s".', name)
        if name in self.hass.data[COMPONENT_DATA]:
            if self.hass.data[COMPONENT_DATA][name]['has_update']:
                remote_info = self.get_all_remote_info()[name]
                remote_file = remote_info[3]
                local_file = self.ha_conf_dir + remote_info[2]
                test_remote_file = requests.get(remote_file)
                if test_remote_file.status_code == 200:
                    with open(local_file, 'wb') as component_file:
                        component_file.write(test_remote_file.content)
                    component_file.close()
                    _LOGGER.info('Upgrade of %s from version %s to version %s complete',
                                 name, self.hass.data[COMPONENT_DATA][name]['local'],
                                 self.hass.data[COMPONENT_DATA][name]['remote'])
                self.hass.data[COMPONENT_DATA][name]['local'] = self.hass.data[COMPONENT_DATA][name]['remote']
                self.hass.data[COMPONENT_DATA][name]['has_update'] = False
                self.hass.data[COMPONENT_DATA][name]['not_local'] = False
                self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[COMPONENT_DATA])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', name)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid component', name)

    def install(self, component):
        """install single component"""
        if component in self.hass.data[COMPONENT_DATA]:
            self.hass.data[COMPONENT_DATA][component]['has_update'] = True
            if '.' in component:
                comppath = '/custom_components/' + component.split('.')[0]
                if not os.path.isdir(self.ha_conf_dir + comppath):
                    os.mkdir(self.ha_conf_dir + comppath)
            self.upgrade_single(component)
            _LOGGER.info('Sucessfully installed %s, make sure you read the documentation on how to set it up.', component)
            return True
        else:
            return False

    def get_all_remote_info(self):
        """Return all remote info if any."""
        remote_info = {}
        for url in self.conf_component_urls:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    for name, component in response.json().items():
                        try:
                            component = [
                                name,
                                component['version'],
                                component['local_location'],
                                component['remote_location'],
                                component['visit_repo'],
                                component['changelog']
                            ]
                            remote_info[name] = component
                        except KeyError:
                            _LOGGER.debug('Gathering remote info for %s failed...', name)
            except:
                _LOGGER.debug('Could not get remote info for url "%s"', url)
        return remote_info

    def get_local_version(self, name, local_path):
        """Return the local version if any."""
        local_version = None
        component_path = self.ha_conf_dir + local_path
        if os.path.isfile(component_path):
            with open(component_path, 'r') as local:
                for line in local.readlines():
                    if '__version__' in line:
                        local_version = line.split("'")[1]
                        break
            local.close()
            if not local_version:
                local_v = False
                _LOGGER.debug('Could not get the local version for %s', name)
            else:
                local_v = local_version
                _LOGGER.debug('Local version of %s is %s', name, local_version)
        else:
            local_v = False
        return local_v