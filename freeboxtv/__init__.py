# -*- coding: utf-8 -*-
from optparse import OptionParser
import subprocess
import tempfile
import logging
import urllib
import signal
import sys
import os

if sys.platform == 'darwin':
    COMMAND_LINE = ['/Applications/VLC.app/Contents/MacOS/VLC',
                    '--m3u-extvlcopt']
else:
    COMMAND_LINE = ['vlc', '--m3u-extvlcopt']
PLAYLIST = 'http://mafreebox.freebox.fr/freeboxtv/playlist.m3u'
TMP_PLAYLIST = os.path.join(tempfile.gettempdir(), 'fbxtv.m3u')
PID = os.path.join(tempfile.gettempdir(), 'fbxtv.pid')

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
    page = urllib.urlopen('http://mafreebox.freebox.fr/freeboxtv/playlist.m3u')
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
            data['url'] = line
            channels[index] = data
            data['raw'] = raw
            index += 1
            raw = ''
    return channels

def main():
    parser = OptionParser()
    parser.add_option("-f", "--fullscreen", dest="fullscreen",
                            action='store_true',
                            default=False,
                            help="full screen mode")
    parser.add_option("-l", "--list", dest="list",
                            action='store_true',
                            default=False,
                            help="list channels")
    parser.add_option("-s", "--stop", dest="stop",
                            action='store_true',
                            default=False,
                            help="stop vlc")
    parser.add_option("-d", "--debug", dest="debug",
                            action='store_true',
                            default=False,
                            help="debug mode")
    options, args = parser.parse_args()
    if options.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Starting in debug mode')
    if options.stop:
        close()
    elif options.list:
        channels = get_channels()
        for k in sorted(channels):
            v = channels.get(k)
            print '%s: %s' % (k, v.get('name'))
    elif not args:
        default(**eval(str(options)))
    else:
        arg = ' '.join(args)
        channels = get_channels()
        if arg.isdigit() and int(arg) in channels:
            open(TMP_PLAYLIST, 'w').write(
                channels.get(int(arg)).get('raw'))
            open_url(TMP_PLAYLIST,**eval(str(options)))
        else:
            arg = arg.lower()
            for k, v in channels.items():
                name = v.get('name').lower()
                if arg in name:
                    open(TMP_PLAYLIST, 'w').write(
                        channels.get(k).get('raw'))
                    open_url(TMP_PLAYLIST,**eval(str(options)))
                    break


