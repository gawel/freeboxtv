# -*- coding: utf-8 -*-
from freeboxtv.utils import Config, BINARY, TMP_PLAYLIST, PID
import subprocess
import logging
import urllib
import signal
import sys
import os

CONFIG = Config.from_file(os.path.expanduser('tv.ini'))

OPTIONS = []
if CONFIG.default.options:
    OPTIONS = CONFIG.default.options.as_list()

COMMAND_LINE = [BINARY]
COMMAND_LINE.extend(OPTIONS)

PLAYLIST = 'http://mafreebox.freebox.fr/freeboxtv/playlist.m3u'

def close():
    if os.path.isfile(PID):
        pid = open(PID).read()
        try:
            os.kill(int(pid), signal.SIGKILL)
        except OSError:
            pass

def open_url(url, fullscreen=False, **options):
    close()
    cmd = COMMAND_LINE + [fullscreen and '-f' or '', url]
    cmd = [a for a in cmd if a]
    logging.debug('Options: %r', options)
    logging.debug('Cmd: %r', cmd)
    if options.get('debug') == True:
        subprocess.call(cmd)
    else:
        stderr = open('/dev/null', 'w')
        pid = subprocess.Popen(cmd, stderr=stderr).pid
        open(PID, 'wb').write(str(pid))

def default(**options):
    open_url(PLAYLIST, **options)

def get_channels():
    page = urllib.urlopen(PLAYLIST)
    channels = dict()
    data = []
    raw = ''
    index = 0
    for line in page.readlines():
        raw += line
        line = line.strip()
        if 'EXTINF' in line:
            data = dict(
                name = line.split(' - ', 1)[1])
        elif 'EXT' not in line:
            name = data['name']
            if not name.endswith(' HD') and not name.endswith('bit)'):
                data['url'] = line
                channels[index] = data
                data['raw'] = raw
                index += 1
            raw = ''
    for k, v in CONFIG.radios.items():
        data = dict(name=k, url=v, raw='%s\n' % v)
        channels[index] = data
        index += 1
    return channels

