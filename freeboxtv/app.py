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
from freeboxtv.utils import Control, Config, config
from freeboxtv import BINARY
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
            '--play-and-exit',
            '--http-src=%s' % VIEWS,
            ]


    def __init__(self):
        self.debug = False
        self.process = None
        self.params = config.fbxplayer
        if 'location' not in self.params:
            self.params.location = os.path.expanduser('~/')
        if 'history_length' not in self.params:
            self.params.history_length = 20
        if 'batching' not in self.params:
            self.params.batching = 25

    def start(self):
        if self.debug:
            args = self.args
            self.process = subprocess.Popen(args)
        else:
            args = self.args + ['--intf=dummy']
            self.process = subprocess.Popen(args, stderr=subprocess.PIPE)
        config.run = dict(pid=self.process.pid)
        config.write()

    def stop(self):
        try:
            os.kill(int(config.run.pid), signal.SIGKILL)
        except OSError, e:
            pass
        except Exception, e:
            log.exception(e)
        self.process = None
        config.write()

    def restart(self):
        self.stop()
        self.start()

    def seek(self, pos):
        self.proxy(path_info='/play.html?type=5&control=seek&seek=%s' % pos)

    @property
    def infos(self):
        return json.loads(self.proxy('/getinfo.html').body)

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
        log.debug(req)
        if headers:
            response.headers.update(resp.headers)
            body = resp.body
            if control:
                body = body.replace('<!-- control -->', control.render())
            if 'text' in resp.content_type:
                log.debug(body)
            return body

player = Player()

class Media(object):

    def __init__(self, filename):
        self.file = filename
        self.name = os.path.basename(filename)[:-4]
        self.type = 3
        self.sub = ''
        sub = filename[:-4] + '.srt'
        if os.path.isfile(sub):
            self.sub = sub
            self.type = 4

    @property
    def prefix(self):
        cfg = Config.from_file('data', md5(self.name).hexdigest())
        if cfg.data and cfg.data.times:
            times = cfg.data.times.as_int()
            if times == 0:
                return '-->'
            else:
                times = times * 2
                if times > 6:
                    times = 6
                return '*'*times
        return ''

    def __repr__(self):
        return '<Media %s>' % (self.prefix, self.file)

app = Bottle()


def batch(control, filenames):
    def url(page=1):
        return  '%s?page=%s' % (request.environ['PATH_INFO'], page)
    page = Page(filenames, page=int(request.GET.get('page', 1)), url=url)
    control.left = '/browser.html?page=%s' % (page.page-1 or 1,)
    control.right = '/browser.html?page=%s' % (page.page+1,)
    return page

@app.route('/playlist.html')
@app.route('/browser.html')
@view('browser')
def index():
    quote = urllib.quote
    basename = os.path.basename

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

@app.route('/keys.html')
@view('settings')
def settings():
    control=Control()
    control.star = '/browser.html'
    control.finalize()
    return dict(locals())

@app.route('/settings.html')
@view('settings')
def settings():
    control=Control()
    control.refresh = ('redirect.html?display_aspect_ratio_def=<var name=display_aspect_ratio>&'
                       'display_scaling_def=<var name=display_scaling>&'
                       'display_aspect_ratio_conversion_def=<var name=display_aspect_ratio_conversion>')
    return dict(locals())

@app.route('/poll.html')
@view('settings')
def poll():
    control=Control()
    infos = dict(player.infos, times=0)
    log.debug(infos)
    name = infos.get('name')
    if name:
        cfg = Config.from_file('data', md5(name).hexdigest())
        if infos['state'] == 'stop':
            if cfg.data.times:
                cfg.data.times = cfg.data.times.as_int() + 1
            else:
                cfg.data.times = 1
            cfg.data.time = 0
            control.refresh = '/browser.html'
        else:
            data = dict(cfg.data.items()) or dict(times=0)
            data.update(infos)
            cfg.data = data
            control.play()
        if 'no_save' not in request.GET:
            cfg.write()
    return dict(locals())

@app.route('/redirect.html')
@view('settings')
def redirect():
    config.display = dict(request.GET.items())
    config.write()
    return index()

@app.route('/sleep.html')
@view('settings')
def sleep():
    config.write()
    if config.cmds and config.cmds.shutdown:
        subprocess.Popen('osascript -e \'tell application "Finder" to sleep\'', shell=True)

@app.route('/play.html')
def play():
    ctrl = request.GET.get('control')
    if ctrl == 'stop':
        player.proxy(headers=False)
        return index()

    control=Control()
    control.play()

    filename = request.GET.get('file')
    if filename and os.path.isfile(filename):
        player.params.location = os.path.dirname(filename)
        history = config.history.filenames.as_list('\n')[-player.params.history_length.as_int():]
        if filename not in history:
            history.append(filename)
            config.history.filenames = history
            config.write()
        else:
            name = os.path.basename(filename)[:-4]
            cfg = Config.from_file('data', md5(name).hexdigest())
            if cfg.data and cfg.data.time.as_int():
                log.debug('seeking')
                control['refresh'] = '2;url=/play.html?type=5&control=seek&seek=%(time)s' % cfg.data

    return player.proxy(control=control)

def main(options, args):
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8080, app)
    print "Serving on port 8080... Hit CTRL+C to stop"
    player.debug = options.debug
    player.restart()
    if options.debug:
        debug(True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        player.stop()

