# -*- coding: utf-8 -*-
from ConfigObject import ConfigObject
import tempfile
import sys
import os

TMP_PLAYLIST = os.path.join(tempfile.gettempdir(), 'fbxtv.m3u')
PID = os.path.join(tempfile.gettempdir(), 'fbxtv.pid')

if sys.platform == 'darwin':
    BINARY = '/Applications/VLC.app/Contents/MacOS/VLC'
else:
    BINARY = 'vlc'

class Config(ConfigObject):

    filename = None

    def write(self, path_or_fd=None):
        if path_or_fd is None and self._filename:
            path_or_fd = self._filename
        if isinstance(path_or_fd, basestring):
            fd = open(path_or_fd, 'w')
        else:
            fd = path_or_fd
        ConfigObject.write(self, fd)
        if isinstance(path_or_fd, basestring):
            fd.close()

    @classmethod
    def from_file(cls, *args, **kwargs):
        filename = os.path.expanduser(os.path.join('~/.freeboxtv', *args))
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        config = cls(defaults=kwargs)
        config.read(filename)
        config._filename = filename
        return config

config = Config.from_file('player.ini')

class Control(dict):

    links = [
        "home",
        "love",
        "love2",
        "mail",
        "mail2",
        "star",
        "blue",
        "green",
        "red",
        "yellow",
        "guide",
        "options",
        "help",
        "info",
        "pause",
        "play",
        "rec",
        "stop",
        "up",
        "down",
        "right",
        "left",
        "star",
        "sharp",
        "prev",
        "next",
        "rev",
        "fwd",
    ]

    metas = [
        "refresh",
        "refresh",
        "disappear",
        "nopicture",
        "channel",
        "settings_page",
        "channel_page",
        "nochannel_page",
        "love_page",

        "home_page",
        "love_page",
        "love2_page",
        "mail_page",
        "mail2_page",
        "star_page",

        "display_aspect_ratio",
        "display_scaling"
    ]

    def __init__(self):
        dict.__init__(self)
        self['stream_location'] = "ts://127.0.0.1"
        self['stream_pcr'] = "68"
        self['stream_vid'] = "68(mp2v)"
        self['stream_aud'] = "69(mp2a,en)"
        self['stream_spu'] = "70(dvbs)"
        self['spu_display'] = "on"
        self['ttx_subtitle_page'] = "889"

        self['settings_page'] = 'settings.html'
        self['home'] = self['home_page'] = 'browser.html'
        self['title'] = self['panel_display'] = 'FBXPLAYER'
        for k, v in config.aliases.items():
            self[k] = v

    def __setattr__(self, attr, value):
        if attr not in self.metas + self.links:
            raise AttributeError(attr)
        if attr == 'refresh':
            value = '0;url=%s' % value
        self[attr] = value

    def play(self):
        self.stop = '/play.html?m=100&type=5&control=stop'
        self.play = '/play.html?type=5&control=pause'
        self.pause = '/play.html?type=5&control=pause'

        self.prev = '/play.html?type=5&self=seek&seek=-10min'
        self.next = '/play.html?type=5&control=seek&seek=+10min'
        self.rev = '/play.html?type=5&control=seek&seek=-1min'
        self.fwd = '/play.html?type=5&control=seek&seek=+1min'

        self.display_scaling = 'letterbox'
        self.display_aspect_ratio = '4/3'

        self.star_page = '/browser.html'

        self['refresh'] = '10;url=/poll.html'

    def finalize(self):
        for k in self.links + self.metas:
            if k not in self and k not in ('refresh',):
                self[k] = '/keys.html?key=%s' % k

    def render(self):
        metas = []
        links = []
        links.append('<title>%s</title>' % self.pop('title'))
        for k, v in self.items():
            if v.startswith('/') and k in self.links:
                links.append('<link rel="%s" href="http://212.27.38.254:8080%s">' % (k, v))
            elif v.startswith('/'):
                links.append('<meta name="%s" content="http://212.27.38.254:8080%s">' % (k, v))
            else:
                metas.append('<meta name="%s" content="%s">' % (k, v))
        return '\n'.join(links+['<services></services>']+metas)

