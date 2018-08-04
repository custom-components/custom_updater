"""
A component which allows you to update your custom cards and components.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_updater
"""

import logging
import os
import subprocess
from datetime import timedelta
import time
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

__version__ = '1.3.0'

_LOGGER = logging.getLogger(__name__)

CONF_TRACK = 'track'
CONF_HIDE_SENSOR = 'hide_sensor'

DOMAIN = 'custom_updater'
CARD_DATA = 'custom_card_data'
COMPONENT_DATA = 'custom_component_data'
INTERVAL = timedelta(days=1)

ATTR_CARD = 'card'
ATTR_COMPONENT = 'component'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_TRACK, default=None):
            vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_HIDE_SENSOR, default=False): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)

CARDS_JSON = 'https://raw.githubusercontent.com/custom-cards/information/master/repos.json'
COMPS_JSON = 'https://raw.githubusercontent.com/custom-components/information/master/repos.json'

def setup(hass, config):
    """Set up this component."""
    conf_track = config[DOMAIN][CONF_TRACK]
    conf_hide_sensor = config[DOMAIN][CONF_HIDE_SENSOR]
    _LOGGER.info('version %s is starting, if you have ANY issues with this, please report'
                 ' them here: https://github.com/custom-components/custom_updater', __version__)

    ha_conf_dir = str(hass.config.path())
    if not conf_track or 'cards' in conf_track:
        card_controller = CustomCards(hass, ha_conf_dir, conf_hide_sensor)
        track_time_interval(hass, card_controller.cache_versions, INTERVAL)
    if not conf_track or 'components' in conf_track:
        components_controller = CustomComponents(hass, ha_conf_dir, conf_hide_sensor)
        track_time_interval(hass, components_controller.cache_versions, INTERVAL)

    def check_all_service(call):
        """Set up service for manual trigger."""
        if not conf_track or 'cards' in conf_track:
            card_controller.cache_versions(call)
        if not conf_track or 'components' in conf_track:
            components_controller.cache_versions(call)

    def update_all_service(call):
        """Set up service for manual trigger."""
        if not conf_track or 'cards' in conf_track:
            card_controller.update_all()
        if not conf_track or 'components' in conf_track:
            components_controller.update_all()

    if not conf_track or 'cards' in conf_track:
        def upgrade_card_service(call):
            """Set up service for manual trigger."""
            card_controller.upgrade_single(call.data.get(ATTR_CARD))
        hass.services.register(DOMAIN, 'upgrade_single_card', upgrade_card_service)

    if not conf_track or 'components' in conf_track:
        def upgrade_component_service(call):
            """Set up service for manual trigger."""
            components_controller.upgrade_single(call.data.get(ATTR_COMPONENT))
        hass.services.register(DOMAIN, 'upgrade_single_component', upgrade_component_service)

    hass.services.register(DOMAIN, 'check_all', check_all_service)
    hass.services.register(DOMAIN, 'update_all', update_all_service)
    return True


class CustomCards:
    """Custom cards controller."""
    def __init__(self, hass, ha_conf_dir, conf_hide_sensor):
        self.hass = hass
        self.cards = None
        self._hide_sensor = conf_hide_sensor
        self.ha_conf_dir = ha_conf_dir
        self.hass.data[CARD_DATA] = {}
        self.cache_versions('now')

    def cache_versions(self, call):
        """Cache"""
        self.cards = self.get_cards()
        self.hass.data[CARD_DATA] = {}
        if self.cards:
            for card in self.cards:
                remoteinfo = self.get_remote_info(card)
                remoteversion = remoteinfo[1]
                localversion = self.get_local_version(remoteinfo[0])
                if localversion:
                    has_update = (remoteversion != False and remoteversion != localversion)
                    not_local = (remoteversion != False and not localversion)
                    self.hass.data[CARD_DATA][card] = {
                        "local": localversion,
                        "remote": remoteversion,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": remoteinfo[3],
                        "change_log": remoteinfo[4],
                    }
                    self.hass.data[CARD_DATA]['domain'] = 'custom_cards'
                    self.hass.data[CARD_DATA]['repo'] = '#'
                    if self._hide_sensor:
                        self.hass.data[CARD_DATA]['hidden'] = True
            self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[CARD_DATA])

    def update_all(self):
        """Update all cards"""
        for card in self.hass.data[CARD_DATA]:
            if card not in ('domain', 'repo'):
                try:
                    if self.hass.data[CARD_DATA][card]['has_update'] and not self.hass.data[CARD_DATA][card]['not_local']:
                        self.upgrade_single(card)
                except:
                    _LOGGER.debug('Skipping upgrade for %s, no update available', card)

    def upgrade_single(self, card):
        """Update one components"""
        _LOGGER.debug('Starting upgrade for "%s".', card)
        if card in self.hass.data[CARD_DATA]:
            if self.hass.data[CARD_DATA][card]['has_update']:
                remoteinfo = self.get_remote_info(card)
                remotefile = remoteinfo[2]
                localfile = self.ha_conf_dir + self.get_card_dir(card) + card + '.js'
                test_remotefile = requests.get(remotefile)
                if test_remotefile.status_code == 200:
                    with open(localfile, 'wb') as card_file:
                        card_file.write(test_remotefile.content)
                    card_file.close()
                    self.update_resource_version(card)
                    _LOGGER.info('Upgrade of %s from version %s to version %s complete',
                                 card, self.hass.data[CARD_DATA][card]['local'],
                                 self.hass.data[CARD_DATA][card]['remote'])
                self.hass.data[CARD_DATA][card]['local'] = self.hass.data[CARD_DATA][card]['remote']
                self.hass.data[CARD_DATA][card]['has_update'] = False
                self.hass.data[CARD_DATA][card]['not_local'] = False
                self.hass.states.set('sensor.custom_card_tracker', time.time(), self.hass.data[CARD_DATA])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', card)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid card', card)

    def update_resource_version(self, card):
        """Updating the ui-lovelace file"""
        localversion = self.hass.data[CARD_DATA][card]['local']
        remoteversion = self.hass.data[CARD_DATA][card]['remote']
        _LOGGER.debug('Updating configuration for %s', card)
        sedcmd = 's/\/'+ card + '.js?v=' + str(localversion) + '/\/'+ card + '.js?v=' + str(remoteversion) + '/'
        _LOGGER.debug('Upgrading card in config from version %s to version %s', localversion, remoteversion)
        subprocess.call(["sed", "-i", "-e", sedcmd, self.ha_conf_dir + '/ui-lovelace.yaml'])

    def get_card_dir(self, card):
        """Get card dir"""
        with open(self.ha_conf_dir + '/ui-lovelace.yaml', 'r') as local:
            for line in local.readlines():
                if '/' + card + '.js' in line:
                    card_dir = line.split(': ')[1].split(card + '.js')[0].replace("local", "www")
                    _LOGGER.debug('Found path "%s" for card "%s"', card_dir, card)
                    break
        return card_dir

    def get_remote_info(self, card):
        """Return the remote info if any."""
        response = requests.get(CARDS_JSON)
        remote_info = [None]
        if response.status_code == 200:
            try:
                remote = response.json()[card]
                remote_info = [card,
                               remote['version'],
                               remote['remote_location'],
                               remote['visit_repo'],
                               remote['changelog']
                              ]
            except:
                _LOGGER.debug('Gathering remote info for %s failed...', card)
                remote = False
        else:
            _LOGGER.debug('Could not get remote info for %s', card)
        return remote_info

    def get_local_version(self, card):
        """Return the local version if any."""
        cardconfig = ''
        with open(self.ha_conf_dir + '/ui-lovelace.yaml', 'r') as local:
            for line in local.readlines():
                if '/' + card + '.js' in line:
                    cardconfig = line
                    break
        if '=' in cardconfig:
            localversion = cardconfig.split('=')[1].split('\n')[0]
            _LOGGER.debug('Local version of %s is %s', card, localversion)
            return localversion
        return False

    def get_cards(self):
        """Get all available cards"""
        _LOGGER.debug('Gathering all available cards.')
        cards = []
        response = requests.get(CARDS_JSON)
        if response.status_code == 200:
            for card in response.json():
                cards.append(card)
        else:
            _LOGGER.debug('Could not reach the remote information repo.')
        return cards


class CustomComponents:
    """Custom components controller."""
    def __init__(self, hass, ha_conf_dir, conf_hide_sensor):
        self.hass = hass
        self.components = None
        self._hide_sensor = conf_hide_sensor
        self.ha_conf_dir = ha_conf_dir
        self.hass.data[COMPONENT_DATA] = {}
        self.cache_versions('now')

    def cache_versions(self, call):
        """Cache"""
        self.components = self.get_components()
        self.hass.data[COMPONENT_DATA] = {}
        if self.components:
            for component in self.components:
                remoteinfo = self.get_remote_info(component)
                remoteversion = remoteinfo[1]
                localversion = self.get_local_version(component, remoteinfo[2])
                if localversion:
                    has_update = (remoteversion != False and remoteversion != localversion)
                    not_local = (remoteversion != False and not localversion)
                    self.hass.data[COMPONENT_DATA][component] = {
                        "local": localversion,
                        "remote": remoteversion,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": remoteinfo[4],
                        "change_log": remoteinfo[5],
                    }
                    self.hass.data[COMPONENT_DATA]['domain'] = 'custom_components'
                    self.hass.data[COMPONENT_DATA]['repo'] = '#'
                    if self._hide_sensor:
                        self.hass.data[COMPONENT_DATA]['hidden'] = True
            self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[COMPONENT_DATA])

    def update_all(self):
        """Update all components"""
        for component in self.hass.data[COMPONENT_DATA]:
            if component not in ('domain', 'repo'):
                try:
                    if self.hass.data[COMPONENT_DATA][component]['has_update'] and not self.hass.data[COMPONENT_DATA][component]['not_local']:
                        self.upgrade_single(component)
                except:
                    _LOGGER.debug('Skipping upgrade for %s, no update available', component)

    def upgrade_single(self, component):
        """Update one components"""
        _LOGGER.debug('Starting upgrade for "%s".', component)
        if component in self.hass.data[COMPONENT_DATA]:
            if self.hass.data[COMPONENT_DATA][component]['has_update']:
                remoteinfo = self.get_remote_info(component)
                remotefile = remoteinfo[3]
                localfile = self.ha_conf_dir + remoteinfo[2]
                test_remotefile = requests.get(remotefile)
                if test_remotefile.status_code == 200:
                    with open(localfile, 'wb') as component_file:
                        component_file.write(test_remotefile.content)
                    component_file.close()
                    _LOGGER.info('Upgrade of %s from version %s to version %s complete',
                                 component, self.hass.data[COMPONENT_DATA][component]['local'],
                                 self.hass.data[COMPONENT_DATA][component]['remote'])
                self.hass.data[COMPONENT_DATA][component]['local'] = self.hass.data[COMPONENT_DATA][component]['remote']
                self.hass.data[COMPONENT_DATA][component]['has_update'] = False
                self.hass.data[COMPONENT_DATA][component]['not_local'] = False
                self.hass.states.set('sensor.custom_component_tracker', time.time(), self.hass.data[COMPONENT_DATA])
            else:
                _LOGGER.debug('Skipping upgrade for %s, no update available', component)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid component', component)

    def get_components(self):
        """Get all available components"""
        _LOGGER.debug('Gathering all available components.')
        components = []
        response = requests.get(COMPS_JSON)
        if response.status_code == 200:
            for component in response.json():
                components.append(component)
        else:
            _LOGGER.debug('Could not reach the remote information repo.')
        return components

    def get_remote_info(self, component):
        """Return the remote info if any."""
        response = requests.get(COMPS_JSON)
        remote_info = [None]
        if response.status_code == 200:
            try:
                remote = response.json()[component]
                remote_info = [component,
                               remote['version'],
                               remote['local_location'],
                               remote['remote_location'],
                               remote['visit_repo'],
                               remote['changelog']
                              ]
            except:
                _LOGGER.debug('Gathering remote info for %s failed...', component)
                remote = False
        else:
            _LOGGER.debug('Could not get remote info for %s', component)
        return remote_info

    def get_local_version(self, component, local_path):
        """Return the local version if any."""
        localversion = None
        componentpath = self.ha_conf_dir + local_path
        if os.path.isfile(componentpath):
            with open(componentpath, 'r') as local:
                for line in local.readlines():
                    if '__version__' in line:
                        localversion = line.split("'")[1]
                        break
            local.close()
            if not localversion:
                localv = False
                _LOGGER.debug('Could not get the local version for %s', component)
            else:
                localv = localversion
                _LOGGER.debug('Local version of %s is %s', component, localversion)
        else:
            localv = False
        return localv
