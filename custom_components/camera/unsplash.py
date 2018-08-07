"""
A camers platform that give you random images from Unsplash presended as a camera feed.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/camera.unsplash
"""
import logging
import mimetypes
import os
import time
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.camera import (PLATFORM_SCHEMA, Camera)

__version__ = '0.3.0'
_LOGGER = logging.getLogger(__name__)

CONF_FILE_PATH = 'file_path'
CONF_API_KEY = 'api_key'
CONF_OUTPUT_DIR = 'output_dir'
CONF_COLLECTION_ID = 'collection_id'
CONF_INTERVAL = 'interval'
CONF_NAME = 'name'

DEFAULT_NAME = 'Unsplash'

DEFAULT_INTERVAL = 10

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_OUTPUT_DIR): cv.string,
    vol.Required(CONF_OUTPUT_DIR, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_COLLECTION_ID, default='None'): cv.string,
    vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Camera that works with local files."""
    file_path = hass.config.path() + config.get(CONF_OUTPUT_DIR) + 'unsplash.jpg'
    api_key = config.get(CONF_API_KEY)
    name = config.get(CONF_NAME)
    collection_id = config.get(CONF_COLLECTION_ID)
    interval = config.get(CONF_INTERVAL)
    camera = UnsplashCamera(name, file_path, api_key, collection_id, interval)
    add_devices([camera])


class UnsplashCamera(Camera):
    """Representation of a local file camera."""

    def __init__(self, name, file_path, api_key, collection_id, interval):
        """Initialize Unsplash Camera component."""
        super().__init__()
        self._name = name
        self._file_path = file_path
        self._api_key = api_key
        self._interval = int(interval) * 60
        self._collection_id = collection_id
        self.get_new_img('init')
        content, _ = mimetypes.guess_type(file_path)
        if content is not None:
            self.content_type = content

    def camera_image(self):
        """Return image response."""
        self.get_new_img('auto')
        try:
            with open(self._file_path, 'rb') as file:
                return file.read()
        except FileNotFoundError:
            _LOGGER.warning("Could not read camera %s image from file: %s",
                            self._name, self._file_path)

    def get_new_img(self, trigger):
        """Download new image if needed"""
        lastchanged = 0
        if os.path.isfile(self._file_path):
            lastchanged = os.stat(self._file_path).st_mtime
        diff = str(time.time() - lastchanged).split('.')[0]
        if int(diff) > int(self._interval) or not os.path.isfile(self._file_path) or trigger == 'init':
            _LOGGER.debug('downloading new img')
            base = 'https://api.unsplash.com/photos/random/'
            if self._collection_id != 'None':
                url = base + '?client_id=' + self._api_key + '&collections=' + self._collection_id
            else:
                url = base + '?client_id=' + self._api_key
            try:
                data = requests.get(url, timeout=5).json()
                downloadurl = data['urls']['regular']
                self._author_name = data['user']['name']
                self._author_user = '@' + data['user']['username']
                file_source = requests.get(downloadurl)
                if file_source.status_code == 200:
                    with open(self._file_path, 'wb+') as camera:
                        camera.write(file_source.content)
                    camera.close()
            except:
                _LOGGER.debug('Failed to update attribs or img.')

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return the camera state attributes."""
        return {
            'source': 'Unsplash',
            'author_name': self._author_name,
            'author_user': self._author_user,
        }
