# -*- coding: utf-8 -*-
from ConfigParser import ConfigParser
from optparse import OptionParser
import logging

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
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Starting in debug mode')

    if options.player:
        from freeboxtv import app
        app.main(options, args)
        return

    from freeboxtv import tv
    if options.stop:
        tv.close()
    elif options.list:
        channels = tv.get_channels()
        for k in sorted(channels):
            v = channels.get(k)
            print '%s: %s' % (k, v.get('name'))
    elif not args:
        tv.default(**eval(str(options)))
    else:
        arg = ' '.join(args)
        channels = tv.get_channels()
        if arg.isdigit() and int(arg) in channels:
            open(tv.TMP_PLAYLIST, 'w').write(
                channels.get(int(arg)).get('raw'))
            tv.open_url(tv.TMP_PLAYLIST,**eval(str(options)))
        else:
            arg = arg.lower()
            for k, v in channels.items():
                name = v.get('name').lower()
                if name.startswith(arg):
                    open(tv.TMP_PLAYLIST, 'w').write(
                        channels.get(k).get('raw'))
                    tv.open_url(tv.TMP_PLAYLIST,**eval(str(options)))
                    break

if __name__ == '__main__':
    main()
