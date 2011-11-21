# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
from optparse import OptionParser
from freeboxtv.player import player
import logging
import tempfile
import os

TMP_PLAYLIST = os.path.join(tempfile.gettempdir(), 'fbxtv.m3u')

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
    parser.add_option("-i", "--info", dest="info",
                            action='store_true',
                            default=False,
                            help="list channels")
    parser.add_option("-s", "--stop", dest="stop",
                            action='store_true',
                            default=False,
                            help="stop vlc")
    parser.add_option("-p", "--freeplayer", dest="player",
                            action='store_true',
                            default=False,
                            help="run the freeplayer")
    parser.add_option("-d", "--debug", dest="debug",
                            action='store_true',
                            default=False,
                            help="debug mode")
    options, args = parser.parse_args()
    if options.debug:
        player.debug = True
        if len(args) == 1 and os.path.isdir(args[0]):
            player.params.location = os.path.abspath(args[0])
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Starting in debug mode')

    if options.player:
        from freeboxtv.app import main
        main()
        return

    if options.stop:
        player.stop()
    elif options.info:
        infos = player.infos
        print('Chan:\t'+infos.name)
        print('State:\t'+infos.state)
        if infos.length:
            print('Pos:\t%smn/%smn'+(time/60, length/60))
        print(infos)
    elif options.list:
        channels = player.channels
        for k in sorted(channels):
            v = channels.get(k)
            print '%s: %s' % (k, v.get('name'))
    elif not args:
        player.default(**eval(str(options)))
    else:
        arg = ' '.join(args)
        channels = player.channels
        if arg.isdigit() and int(arg) in channels:
            open(TMP_PLAYLIST, 'w').write(
                channels.get(int(arg)).get('raw'))
            player.open_url(TMP_PLAYLIST,**eval(str(options)))
        else:
            arg = arg.lower()
            for k, v in channels.items():
                name = v.get('name').lower()
                if name.startswith(arg):
                    open(TMP_PLAYLIST, 'w').write(
                        channels.get(k).get('raw'))
                    player.open_url(TMP_PLAYLIST, **eval(str(options)))
                    break

if __name__ == '__main__':
    main()
