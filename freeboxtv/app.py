# -*- coding: utf-8 -*-
import os
import sys
import json
import bottle
import urllib
import signal
import logging as log
from glob import glob
from webhelpers.paginate import Page
from freeboxtv.utils import Control, Params
from freeboxtv.player import Media
from freeboxtv.player import player
from freeboxtv import config
from bottle import *

exts = ['.mp4', '.avi']

app = Bottle()


def batch(control, filenames, path_info='/browser'):
    i = 1
    if player.params.latest in filenames:
        i = filenames.index(player.params.latest)
        i = len(filenames)/20
    def url(page=1):
        return  '%s?page=%s' % (request.environ['PATH_INFO'], page)
    page = Page(filenames, page=int(request.GET.get('page', i)), url=url)
    control.left = '%s?page=%s' % (path_info, page.page-1 or 1,)
    control.right = '%s?page=%s' % (path_info, page.page+1,)
    return page


@app.route('/keys')
@view('settings')
def keys():
    control=Control()
    control.star = '/browser'
    control.finalize()
    return locals()


@app.route('/settings.html')
@app.route('/browser')
@view('browser')
def index():
    quote = urllib.quote
    basename = os.path.basename

    if player.params.latest:
        root = request.GET.get('root', os.path.dirname(player.params.latest))
    else:
        root = request.GET.get('root', player.params.location)
    root = os.path.realpath(root)
    player.params.location = root

    dirnames = []
    filenames = []
    for root, dirnames, filenames in os.walk(root):
        break
    dirnames = [os.path.join(root, d) for d in dirnames if not d.startswith('.')]
    filenames = [os.path.join(root, d) for d in sorted(filenames) \
            if not d.startswith('.') and d.lower()[-4:] in exts]

    control=Control()
    control.star_page = '/browser?root=%s' % quote(os.path.dirname(root))
    page = batch(control, filenames)
    filenames = [Media(f) for f in page.items]

    return locals()


@app.route('/history')
@view('browser')
def history():
    control=Control()
    control.star_page = '/browser'
    history = config.history.filenames.as_list('\n')
    page = batch(control, list(reversed(history)), path_info='/history')
    filenames = [Media(f) for f in page.items]
    dirnames = []
    quote = urllib.quote
    return locals()


@app.route('/control')
@view('control')
def control():
    infos = player.infos
    name = infos.name
    if name == 'current_node_name':
        return index()
    length = infos.length
    if 'seek' in request.GET:
        if length:
            pos = int(float(request.GET['seek'])*length/100)
            player.call('seek', str(pos))
            infos = player.infos
    if length:
        time = infos.time
        pos = int(float(time)/length*100)
    else:
        pos = 0
    length = '%smn' % (length/60)
    poll(auto=False)
    control=Control()
    control.star = '/poll'
    control.info = '/poll'
    return locals()


@app.route('/poll')
@view('settings')
def poll(auto=True):
    control=Control()
    infos = player.infos
    name = infos.name
    if name and name != 'current_node_name':
        media = Media(name=name)
        rest = infos.length - infos.time
        if infos.state == 'stop':
            if auto or rest < 120:
                log.debug('Media ended')
                if media.times:
                    times = media.times.as_int() + 1
                else:
                    times = 1
                media.data.update(times=times, time=0)
            control.refresh = '/browser'
        elif infos.state == 'playing':
            media.data.update(infos)
            delay = 30
            if rest < 180:
                delay = 3
            control.play(poll=delay)
        log.debug('Saving %r', media)
        media.write()
    else:
        control.refresh = '/browser'
    return locals()


@app.route('/cmds/:cmd')
@app.route('/cmds/:cmd/:arg')
@view('settings')
def call(cmd, arg=None):
    if arg:
        player.call(cmd, arg)
    else:
        player.call(cmd)
    if cmd == 'stop':
        poll(auto=False)
        return index()
    return poll()


@app.route('/play/:name')
@view('settings')
def play(name):
    media = Media(name=name)
    if media.file and os.path.isfile(media.file):
        control=Control()
        control.play(poll=2)
        filename = media.file
        player.params.location = os.path.dirname(filename)
        player.params.latest = filename
        history = config.history.filenames.as_list('\n')[-player.params.history_length.as_int():]
        if filename not in history:
            history.append(filename)
            config.history.filenames = history
            config.write()
        seek = media.play()
        if seek:
            control.refresh = (3, '/cmds/seek/%s' % seek)
        return locals()
    return index()


def main():
    import socket
    from wsgiref import simple_server

    class WSGIRequestHandler(simple_server.WSGIRequestHandler):
        """A WSGIRequestHandler who log to a logger"""

        def log_message(self, format, *args):
            log.debug(format % args)

    player.stop()
    player.start()
    if player.debug:
        debug(True)
    try:
        httpd = simple_server.make_server(
                    '', 8080, app,
                    handler_class=WSGIRequestHandler)
        print "Serving on port 8080... Hit CTRL+C to stop"
        httpd.serve_forever()
    except KeyboardInterrupt:
        player.stop()
    except socket.error, e:
        print e

