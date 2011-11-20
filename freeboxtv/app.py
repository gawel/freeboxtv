# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import bottle
import urllib
import signal
from hashlib import md5
import logging as log
from glob import glob
import subprocess
from wsgiproxy.exactproxy import proxy_exact_request
from webhelpers.paginate import Page
from webob import Request as WebObRequest
from freeboxtv.utils import Control, Params, Config, config
from freeboxtv.utils import BINARY, PID
from bottle import *

VIEWS = os.path.join(os.path.dirname(__file__), 'views')
bottle.TEMPLATE_PATH = [VIEWS]

exts = ['.mp4', '.avi']

class Player(object):

    args = [BINARY,
            '--extraintf=http',
            '--http-host=:8070',
            '--sout=#std',
            '--sout-standard-access=udp',
            '--sout-standard-mux=ts',
            '--sout-standard-dst=212.27.38.253:1234',
            '--sout-ts-pid-video=68',
            '--sout-ts-pid-audio=69',
            '--sout-ts-pid-spu=70',
            '--sout-ts-pcr=80',
            '--sout-ts-dts-delay=400',
            '--subsdec-encoding=ISO-8859-1',
            '--sout-transcode-maxwidth=720',
            '--sout-transcode-maxheight=576',
            '--http-src=%s' % VIEWS,
            ]


    def __init__(self):
        self.debug = False
        self.params = config.fbxplayer
        if 'location' not in self.params:
            self.params.location = os.path.expanduser('~/')
        if 'history_length' not in self.params:
            self.params.history_length = 20

    def start(self):
        if self.debug:
            args = self.args
            process = subprocess.Popen(args)
        else:
            args = self.args + ['--intf=dummy']
            process = subprocess.Popen(args, stderr=subprocess.PIPE)
        open(PID, 'w').write(str(process.pid))
        config.write()

    @classmethod
    def stop(self):
        if os.path.isfile(PID):
            pid = open(PID).read()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass
        config.write()

    def hup(self):
        if os.path.isfile(PID):
            pid = open(PID).read()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass

    def restart(self):
        log.debug('restarting')
        self.stop()
        self.start()
        log.debug('restarted')

    def seek(self, pos):
        self.proxy(path_info='/play.html?type=5&control=seek&seek=%s' % pos)

    @property
    def is_playing(self):
        return self.infos.get('state', 'playing') != 'stop'

    @property
    def infos(self):
        return Params(json.loads(self.proxy('/getinfo.html').body))

    def proxy(self, path_info=None, control=None, headers=True):
        if path_info:
            req = WebObRequest.blank(path_info)
        else:
            req = WebObRequest(request.environ)
        req.environ['SERVER_NAME'] = '127.0.0.1'
        req.environ['SERVER_PORT'] = '8070'
        req.environ['HOST'] = '127.0.0.1:8070'
        resp = req.get_response(proxy_exact_request)
        if path_info:
            return resp
        if "connection" in resp.headers:
            del resp.headers['connection']
        #log.debug(req)
        if headers:
            response.headers.update(resp.headers)
            body = resp.body
            if control:
                body = body.replace('<!-- control -->', control.render())
            if 'text' in resp.content_type:
                #log.debug(body)
                pass
            return body

player = Player()

class Media(object):

    def __init__(self, filename=None, name=None):
        if name is None:
            name, _ = os.path.splitext(os.path.basename(filename))
            self.config = Config.from_file('data', md5(name).hexdigest())
            self.data = data = self.config.data
            data.name = name
            data.file = filename
            data.type = 2
            data.sub = ''
            sub = os.path.splitext(filename)[0] + '.srt'
            if os.path.isfile(sub):
                data.sub = sub
                data.type = 3
            self.config.write()
        else:
            self.config = Config.from_file('data', md5(name).hexdigest())
            self.data = self.config.data

    def __getattr__(self, attr):
        return self.data[attr]

    def write(self):
        self.config.write()

    @property
    def focused(self):
        return player.params.latest == self.file and 'focused' or ''

    @property
    def prefix(self):
        if self.times:
            times = self.times.as_int()
            if times == 0:
                return '-->'
            else:
                times = times * 2
                if times > 6:
                    times = 6
                return '*'*times
        return ''

    def __repr__(self):
        return '<Media %s %s - %s>' % (self.prefix, self.data, self.config.filename)

app = Bottle()

def batch(control, filenames):
    i = 1
    if player.params.latest in filenames:
        i = filenames.index(player.params.latest)
        i = len(filenames)/20
    def url(page=1):
        return  '%s?page=%s' % (request.environ['PATH_INFO'], page)
    page = Page(filenames, page=int(request.GET.get('page', i)), url=url)
    control.left = '/browser.html?page=%s' % (page.page-1 or 1,)
    control.right = '/browser.html?page=%s' % (page.page+1,)
    return page

@app.route('/settings.html')
@view('settings')
def settings():
    if request.GET:
        config.display = dict(request.GET.items())
        config.write()
        return index()
    control=Control()
    control.refresh = ('settings.html?display_aspect_ratio_def=<var name=display_aspect_ratio>&'
                       'display_scaling_def=<var name=display_scaling>&'
                       'display_aspect_ratio_conversion_def=<var name=display_aspect_ratio_conversion>')
    return dict(locals())

@app.route('/keys.html')
@view('settings')
def keys():
    control=Control()
    control.star = '/browser.html'
    control.finalize()
    return dict(locals())

@app.route('/playlist.html')
@app.route('/browser.html')
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
    control.star_page = '/browser.html?root=%s' % quote(os.path.dirname(root))
    page = batch(control, filenames)
    filenames = [Media(f) for f in page.items]

    sdelay = 0

    return dict(locals())

@app.route('/history.html')
@view('browser')
def history():
    control=Control()
    control.star_page = '/browser.html'
    history = config.history.filenames.as_list('\n')
    page = batch(control, list(reversed(history)))
    filenames = [Media(f) for f in page.items]
    dirnames = []
    quote = urllib.quote
    return dict(locals())

@app.route('/control.html')
@view('control')
def control():
    infos = player.infos
    name = infos.name
    if name == 'current_node_name':
        return index()
    poll(auto=False)
    control=Control()
    length = infos.length
    time = infos.time
    control.star = '/poll.html'
    control.info = '/poll.html'
    if 'seek' in request.GET:
        if length:
            player.seek(int(float(request.GET['seek'])*length/100))
            control.refresh = (1, '/control.html')
            return template('settings.html', **locals())
    if length:
        pos = int(float(time)/length*100)
    else:
        pos = 0
    length = '%smn' % (length/60)
    return dict(locals())

@app.route('/poll.html')
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
                    media.times = media.times.as_int() + 1
                else:
                    media.times = 1
                media.time = 0
            control.refresh = '/browser.html'
        elif infos.state == 'playing':
            media.data.update(infos)
            delay = 30
            if rest < 180:
                delay = 3
            control.play(poll=delay)
        log.debug('Saving %s', media)
        media.write()
    else:
        control.refresh = '/browser.html'
    return dict(locals())

@app.route('/play.html')
def play():
    ctrl = request.GET.get('control')
    if ctrl == 'stop':
        player.proxy(headers=False)
        poll(auto=False)
        return index()

    control=Control()
    control.play(poll=2)

    filename = request.GET.get('file')
    log.debug('Play %s', filename)
    if filename and os.path.isfile(filename):
        player.params.location = os.path.dirname(filename)
        player.params.latest = filename
        history = config.history.filenames.as_list('\n')[-player.params.history_length.as_int():]
        if filename not in history:
            history.append(filename)
            config.history.filenames = history
            config.write()
        name, _ = os.path.splitext(os.path.basename(filename))
        media = Media(name=name)
        log.debug('Play %s', media)
        if media.time and media.time.as_int():
            log.debug('seeking %s', media)
            control.refresh = (2, '/play.html?type=5&control=seek&seek=%(time)s' % media.data)

    return player.proxy(control=control)


def main(options, args):
    import socket
    from wsgiref import simple_server

    class WSGIRequestHandler(simple_server.WSGIRequestHandler):
        """A WSGIRequestHandler who log to a logger"""

        def log_message(self, format, *args):
            log.debug(format % args)

    player.debug = options.debug
    player.restart()
    if options.debug:
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

