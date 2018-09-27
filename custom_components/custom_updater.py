"""
A component which allows you to update your custom cards and components.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/custom_updater
"""
import fileinput
import logging
import os
import re
import sys
from datetime import timedelta

import requests
from requests import RequestException
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval
import yaml

__version__ = '2.7.2'

_LOGGER = logging.getLogger(__name__)

CONF_TRACK = 'track'
CONF_HIDE_SENSOR = 'hide_sensor'
CONF_SHOW_INSTALLABLE = 'show_installable'
CONF_CARD_CONFIG_URLS = 'card_urls'
CONF_COMPONENT_CONFIG_URLS = 'component_urls'

DOMAIN = 'custom_updater'
CARD_DATA = 'custom_card_data'
COMP_DATA = 'custom_COMP_DATA'
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

GH_RAW = 'https://raw.githubusercontent.com/'
DEFAULT_CARD_URL = GH_RAW + 'custom-cards/information/master/repos.json'
DEFAULT_COMPONENT_URL = (GH_RAW + 'custom-components/' +
                         'information/master/repos.json')


def setup(hass, config):
    """Set up this component."""
    conf_track = config[DOMAIN][CONF_TRACK]
    conf_hide_sensor = config[DOMAIN][CONF_HIDE_SENSOR]
    config_show_installabe = config[DOMAIN][CONF_SHOW_INSTALLABLE]
    conf_card_urls = [DEFAULT_CARD_URL] + config[DOMAIN][CONF_CARD_CONFIG_URLS]
    conf_component_urls = ([DEFAULT_COMPONENT_URL] +
                           config[DOMAIN][CONF_COMPONENT_CONFIG_URLS])

    _LOGGER.info('if you have ANY issues with this, please report them here:'
                 ' https://github.com/custom-components/custom_updater')

    if 'cards' in conf_track:
        card_controller = CustomCards(hass,
                                      conf_hide_sensor, conf_card_urls,
                                      config_show_installabe)
        track_time_interval(hass, card_controller.cache_versions, INTERVAL)
    if 'components' in conf_track:
        components_controller = CustomComponents(hass,
                                                 conf_hide_sensor,
                                                 conf_component_urls,
                                                 config_show_installabe)
        track_time_interval(hass, components_controller.cache_versions,
                            INTERVAL)

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
        """Install single component/card."""
        element = call.data.get(ATTR_ELEMENT)
        _LOGGER.debug('Installing %s', element)
        card_controller.install(element)
        components_controller.install(element)

    if not conf_track or 'cards' in conf_track:
        def upgrade_card_service(call):
            """Set up service for manual trigger."""
            card_controller.upgrade_single(call.data.get(ATTR_CARD), 'auto')
        hass.services.register(DOMAIN, 'upgrade_single_card',
                               upgrade_card_service)

    if not conf_track or 'components' in conf_track:
        def upgrade_component_service(call):
            """Set up service for manual trigger."""
            components_controller.upgrade_single(call.data.get(ATTR_COMPONENT))
        hass.services.register(DOMAIN, 'upgrade_single_component',
                               upgrade_component_service)

    hass.services.register(DOMAIN, 'check_all', check_all_service)
    hass.services.register(DOMAIN, 'update_all', update_all_service)
    hass.services.register(DOMAIN, 'install', install_service)
    return True


class CustomCards():
    """Custom cards controller."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, hass, conf_hide_sensor,
                 conf_card_urls, config_show_installabe):
        """Initialize."""
        self.hass = hass
        self._hide_sensor = conf_hide_sensor
        self._config_show_installable = config_show_installabe
        self.ha_conf_dir = str(hass.config.path())
        self.conf_card_urls = conf_card_urls
        self.cards = None
        self._updatable = 0
        self._lovelace_gen = self.get_lovelace_gen()
        self._conf_file_path = self.get_conf_file_path()
        self.hass.data[CARD_DATA] = {}
        self.cache_versions()

    def get_lovelace_gen(self):
        """Get lovelace-gen true if in use."""
        conf_file = os.path.join(self.ha_conf_dir, 'ui-lovelace.yaml')
        lovelace_dir = os.path.join(self.ha_conf_dir, 'lovelace')
        if os.path.isfile(conf_file) and os.path.isdir(lovelace_dir):
            with open(conf_file, 'r') as local:
                for line in local.readlines():
                    if 'generated by lovelace-gen.py' in line:
                        _LOGGER.debug('Found evidence of lovelace-gen usage, '
                                      'assuming that is being used.')
                        return True
        return False

    def cache_versions(self):
        """Cache."""
        self.cards = self.get_all_remote_info()
        self.hass.data[CARD_DATA] = {}
        self.hass.data[CARD_DATA]['domain'] = 'custom_cards'
        self.hass.data[CARD_DATA]['repo'] = '#'
        self.hass.data[CARD_DATA]['has_update'] = []
        self._updatable = 0
        if self._hide_sensor:
            self.hass.data[CARD_DATA]['hidden'] = True
        if self.cards:
            for name, card in self.cards.items():
                remote_version = card[1]
                local_version = self.get_local_version(card[0])
                if self._config_show_installable:
                    show = remote_version
                else:
                    show = local_version
                if show:
                    has_update = (remote_version and remote_version !=
                                  local_version and remote_version != '')
                    not_local = (remote_version and not local_version)
                    if has_update and not not_local:
                        self._updatable = self._updatable + 1
                        self.hass.data[CARD_DATA]['has_update'].append(name)
                    self.hass.data[CARD_DATA][name] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": card[3],
                        "change_log": card[4],
                    }
            self.hass.states.set('sensor.custom_card_tracker', self._updatable,
                                 self.hass.data[CARD_DATA])

    def update_all(self):
        """Update all cards."""
        for name in self.hass.data[CARD_DATA]:
            if name not in ('domain', 'repo', 'hidden'):
                try:
                    if (self.hass.data[CARD_DATA][name]['has_update'] and
                            not self.hass.data[CARD_DATA][name]['not_local']):
                        self.upgrade_single(name, 'auto')
                except KeyError:
                    _LOGGER.debug('No update available for %s', name)

    def upgrade_single(self, name, method):
        """Update one components."""
        _LOGGER.debug('Starting upgrade for "%s".', name)
        if name in self.hass.data[CARD_DATA]:
            if self.hass.data[CARD_DATA][name]['has_update']:
                try:
                    remote_info = self.get_all_remote_info()[name]
                    remote_file = remote_info[2]
                    if method == 'auto':
                        local_file = os.path.join(self.ha_conf_dir,
                                                  self.get_card_dir(name),
                                                  name + '.js')
                    else:
                        if self._lovelace_gen:
                            local_file = os.path.join(self.ha_conf_dir,
                                                      'lovelace',
                                                      name + '.js')
                        else:
                            local_file = os.path.join(self.ha_conf_dir,
                                                      'www',
                                                      name + '.js')
                    test_remote_file = requests.get(remote_file)
                    if test_remote_file.status_code == 200:
                        with open(local_file, 'wb') as card_file:
                            card_file.write(test_remote_file.content)
                        self.upgrade_lib(name, method)
                        if method == 'auto':
                            self.update_resource_version(name)
                        _LOGGER.info('%s upgrade from %s to %s complete',
                                     name,
                                     self.hass.data[CARD_DATA][name]['local'],
                                     self.hass.data[CARD_DATA][name]['remote'])
                        remote = self.hass.data[CARD_DATA][name]['remote']
                        self.hass.data[CARD_DATA][name]['local'] = remote
                        self.hass.data[CARD_DATA][name]['has_update'] = False
                        self.hass.data[CARD_DATA][name]['not_local'] = False
                        self._updatable = self._updatable - 1
                        self.hass.states.set('sensor.custom_card_tracker',
                                             self._updatable,
                                             self.hass.data[CARD_DATA])
                except PermissionError:
                    _LOGGER.error('Premission denied!')
            else:
                _LOGGER.debug('No update available for %s', name)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid card', name)

    def upgrade_lib(self, name, method):
        """Update one components."""
        _LOGGER.debug('Downloading lib for %s if available', name)
        remote_info = self.get_all_remote_info()[name]
        remote_file = remote_info[2][:-3] + '.lib.js'
        if method == 'auto':
            local_file = os.path.join(self.ha_conf_dir,
                                      self.get_card_dir(name),
                                      name + '.lib.js')
        else:
            if self._lovelace_gen:
                local_file = os.path.join(self.ha_conf_dir,
                                          'lovelace',
                                          name + '.lib.js')
            else:
                local_file = os.path.join(self.ha_conf_dir,
                                          'www',
                                          name + '.lib.js')
        test_remote_file = requests.get(remote_file)
        if test_remote_file.status_code == 200:
            with open(local_file, 'wb') as card_file:
                card_file.write(test_remote_file.content)
            _LOGGER.info('Successfully upgraded lib for %s', name)

    def install(self, card):
        """Install single card."""
        if card in self.hass.data[CARD_DATA]:
            self.hass.data[CARD_DATA][card]['has_update'] = True
            self.upgrade_single(card, 'manual')
            _LOGGER.info('Successfully installed %s', card)

    @staticmethod
    def replace_all(file, search, replace):
        """Replace all occupancies of search in file."""
        for line in fileinput.input(file, inplace=True):
            if search in line:
                line = line.replace(search, replace)
            sys.stdout.write(line)

    def update_resource_version(self, name):
        """Update the ui-lovelace file."""
        local_version = self.hass.data[CARD_DATA][name]['local']
        remote_version = self.hass.data[CARD_DATA][name]['remote']
        _LOGGER.debug('Updating configuration for %s', name)
        _LOGGER.debug('Upgrading card in config from version %s to version %s',
                      local_version, remote_version)
        resource_path = self.get_resource_path()
        self.replace_all(
            resource_path,
            '{}.js?v={}'.format(name, local_version),
            '{}.js?v={}'.format(name, remote_version))

    def get_resource_path(self):
        """Get resource file."""
        if os.path.isfile(self._conf_file_path):
            with open(self._conf_file_path, 'r') as local:
                pattern = re.compile(r"^resources:\s!include\s(.*)$")
                for line in local.readlines():
                    matcher = pattern.match(line)
                    if matcher:
                        resource_path = self._normalize_path(matcher.group(1))
                        return os.path.join(self.ha_conf_dir, resource_path)
        return self._conf_file_path

    @staticmethod
    def _normalize_path(path):
        path = path.replace('/', os.path.sep) \
            .replace('\\', os.path.sep)

        if path.startswith(os.path.sep):
            path = path[1:]

        return path

    def get_card_dir(self, name):
        """Return card dir if any."""
        resources = self.get_resources()
        if resources is not None:
            if self._lovelace_gen:
                extra = "lovelace"
                pattern = re.compile(r"^!resource\s(.*)/" + name +
                                     r"\.js(\?v=.*)?$")
            else:
                extra = ""
                pattern = re.compile("^(.*)/" + name + r"\.js\?v=.*$")
            for resource in resources:
                if resource['url'] is not None:
                    matcher = pattern.match(resource['url'])
                    if matcher:
                        card_js_path = self._normalize_path(matcher.group(1))\
                            .replace("local", "www")
                        card_dir = os.path.join(extra, card_js_path)
                        _LOGGER.debug('Found path "%s" for card "%s"',
                                      extra, name)
                        return card_dir
        return None

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
                            _LOGGER.debug('Could not get remote info for %s',
                                          name)
            except RequestException:
                _LOGGER.debug('Could not get remote info for url "%s"', url)
        return remote_info

    def get_conf_file_path(self):
        """Get conf file."""
        if self._lovelace_gen:
            return os.path.join(self.ha_conf_dir, 'lovelace', 'main.yaml')
        return os.path.join(self.ha_conf_dir, 'ui-lovelace.yaml')

    def get_resources(self):
        """Get resources."""
        yaml.add_constructor(u'!resource', env_constructor)
        if os.path.isfile(self._conf_file_path):
            with open(self._conf_file_path, 'r') as local:
                content = yaml.load(local)
                if content['resources'] is not None:
                    resources = []
                    for tuples in content['resources']:
                        resource = {}
                        for key, value in tuples.items():
                            resource.setdefault(key, value)
                        resources.append(resource)
                    _LOGGER.debug(resources)
                    return resources
        return []

    def get_local_version(self, name):
        """Return the local version if any."""
        resources = self.get_resources()
        if resources is not None:
            pattern = re.compile("^.*/" + name + r"\.js\?v=(.*)$")
            for resource in resources:
                if resource['url'] is not None:
                    matcher = pattern.match(resource['url'])
                    if matcher:
                        _LOGGER.debug('Local version of %s is %s',
                                      name, matcher.group(1))
                        return matcher.group(1)
        return None


class CustomComponents():
    """Custom components controller."""

    def __init__(self, hass, conf_hide_sensor,
                 conf_component_urls, config_show_installable):
        """Initialize."""
        self.hass = hass
        self._hide_sensor = conf_hide_sensor
        self._config_show_installable = config_show_installable
        self.ha_conf_dir = str(hass.config.path())
        self.conf_component_urls = conf_component_urls
        self.components = None
        self._updatable = 0
        self.hass.data[COMP_DATA] = {}
        self.cache_versions()

    def cache_versions(self):
        """Cache."""
        self.components = self.get_all_remote_info()
        self.hass.data[COMP_DATA] = {}
        self.hass.data[COMP_DATA]['domain'] = 'custom_components'
        self.hass.data[COMP_DATA]['repo'] = '#'
        self.hass.data[COMP_DATA]['has_update'] = []
        self._updatable = 0
        if self._hide_sensor:
            self.hass.data[COMP_DATA]['hidden'] = True
        if self.components:
            for name, component in self.components.items():
                remote_version = component[1]
                local_version = self.get_local_version(name, component[2])
                if self._config_show_installable:
                    show = remote_version
                else:
                    show = local_version
                if show:
                    has_update = (remote_version and
                                  remote_version != local_version)
                    not_local = (remote_version and not local_version)
                    if has_update and not not_local:
                        self._updatable = self._updatable + 1
                        self.hass.data[COMP_DATA]['has_update'].append(name)
                    self.hass.data[COMP_DATA][name] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": component[4],
                        "change_log": component[5],
                    }
            self.hass.states.set('sensor.custom_component_tracker',
                                 self._updatable, self.hass.data[COMP_DATA])

    def update_all(self):
        """Update all components."""
        for name in self.hass.data[COMP_DATA]:
            if name not in ('domain', 'repo', 'hidden'):
                try:
                    if (self.hass.data[COMP_DATA][name]['has_update'] and
                            not self.hass.data[COMP_DATA][name]['not_local']):
                        self.upgrade_single(name)
                except KeyError:
                    _LOGGER.debug('No update available for %s', name)

    def upgrade_single(self, name):
        """Update one components."""
        _LOGGER.debug('Starting upgrade for "%s".', name)
        if name in self.hass.data[COMP_DATA]:
            if self.hass.data[COMP_DATA][name]['has_update']:
                remote_info = self.get_all_remote_info()[name]
                remote_file = remote_info[3]
                local_file = os.path.join(self.ha_conf_dir, remote_info[2])
                test_remote_file = requests.get(remote_file)
                if test_remote_file.status_code == 200:
                    try:
                        with open(local_file, 'wb') as component_file:
                            component_file.write(test_remote_file.content)
                        component_file.close()
                        _LOGGER.info('%s upgrade from %s to %s complete',
                                     name,
                                     self.hass.data[COMP_DATA][name]['local'],
                                     self.hass.data[COMP_DATA][name]['remote'])
                        remote = self.hass.data[COMP_DATA][name]['remote']
                        self.hass.data[COMP_DATA][name]['local'] = remote
                        self.hass.data[COMP_DATA][name]['has_update'] = False
                        self.hass.data[COMP_DATA][name]['not_local'] = False
                        self._updatable = self._updatable - 1
                        self.hass.states.set('sensor.custom_component_tracker',
                                             self._updatable,
                                             self.hass.data[COMP_DATA])
                    except PermissionError:
                        _LOGGER.error('Premission denied!')
            else:
                _LOGGER.debug('No update available for %s', name)
        else:
            _LOGGER.error('Upgrade failed, "%s" is not a valid component',
                          name)

    def install(self, component):
        """Install single component."""
        if component in self.hass.data[COMP_DATA]:
            self.hass.data[COMP_DATA][component]['has_update'] = True
            matcher = re.compile(r"^(.*)\..*$").match(component)
            if matcher:
                component_path = os.path.join(self.ha_conf_dir,
                                              'custom_components',
                                              matcher.group(1))
                if not os.path.isdir(component_path):
                    os.mkdir(component_path)
            self.upgrade_single(component)
            _LOGGER.info('Successfully installed %s', component)

    @staticmethod
    def _normalize_path(path):
        path = path.replace('/', os.path.sep)\
            .replace('\\', os.path.sep)

        if path.startswith(os.path.sep):
            path = path[1:]

        return path

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
                                self._normalize_path(
                                    component['local_location']),
                                component['remote_location'],
                                component['visit_repo'],
                                component['changelog']
                            ]
                            remote_info[name] = component
                        except KeyError:
                            _LOGGER.debug('Could not get remote info for %s',
                                          name)
            except RequestException:
                _LOGGER.debug('Could not get remote info for url "%s"', url)
        return remote_info

    def get_local_version(self, name, local_path):
        """Return the local version if any."""
        component_path = os.path.join(self.ha_conf_dir, local_path)
        if os.path.isfile(component_path):
            with open(component_path, 'r') as local:
                pattern = re.compile(r"^__version__\s*=\s*['\"](.*)['\"]$")
                for line in local.readlines():
                    matcher = pattern.match(line)
                    if matcher:
                        _LOGGER.debug('Local version of %s is %s',
                                      name,
                                      matcher.group(1))
                        return matcher.group(1)
        _LOGGER.debug('Could not get the local version for %s', name)
        return False


def env_constructor(self, loader, node):
    """Add custom node to yaml loader."""
    value = loader.construct_scalar(node)
    return os.environ.get(value)
