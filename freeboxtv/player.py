# -*- coding: utf-8 -*-
import os
import sys
import json
import signal
import urllib
import tempfile
import subprocess
import logging as log
from hashlib import md5
from freeboxtv import config
from webob import Request
from ConfigObject import ConfigObject
from freeboxtv.utils import Params, Control
from wsgiproxy.exactproxy import proxy_exact_request
import bottle

if sys.platform == 'darwin':
    BINARY = '/Applications/VLC.app/Contents/MacOS/VLC'
else:
    BINARY = 'vlc'

bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__), 'views')]

class Media(object):

    def __init__(self, filename=None, name=None):
        if name is None:
            name, _ = os.path.splitext(os.path.basename(filename))
        h = md5(name).hexdigest()
        data = os.path.expanduser(os.path.join('~/.freeboxtv', 'data',
                                        h[:2], h[2:4], h[4:6], h))
        if not os.path.isdir(os.path.dirname(data)):
            os.makedirs(os.path.dirname(data))
        self.config = ConfigObject(filename=data)
        self.data = data = self.config.data
        self.write = self.config.write
        if not self.file and filename:
            data.name = name
            data.file = filename
            self.write()

    def __getattr__(self, attr):
        return self.data[attr]

    @property
    def focused(self):
        return player.params.latest == self.file and 'focused' or ''

    @property
    def sub(self):
        sub = os.path.splitext(self.file)[0] + '.srt'
        if os.path.isfile(sub):
            return sub
        return None

    @property
    def prefix(self):
        if self.time and self.time.as_int() > 0:
            return '-->'
        if self.times:
            times = self.times.as_int()
            if times:
                return '*'
        return ''

    def play(self):
         cmd = (' :sout=#transcode:std '
                ':sout-transcode-ab=256 '
                ':sout-transcode-acodec=mpga '
                ':sout-transcode-channels=2 '
                ':sout-transcode-vb=9000 '
                ':sout-transcode-vcodec=mp2v '
                ':sout-transcode-vt=1000000 '
                ':sout-transcode-fps=25.0 '
                ':sout-ffmpeg-keyint=24 '
                ':sout-ffmpeg-interlace '
                ':no-sout-ffmpeg-interlace-me '
                ':file-caching=2000 '
                ':sout-transcode-soverlay ')
         def escape(f):
             f = f.replace("'", r"\'")
             return f
         try:
             delay = self.sub_delay.as_int()
         except:
             pass
         else:
             if delay != 0:
                 cmd += ':sub-delay=%s ' % delay
         if self.sub:
             cmd += ':no-sub-autodetect-file :sub-file=%s ' % escape(self.sub)
         player.call('play', "'%s %s' '%s'" % (escape(self.file), cmd, self.name),
                     media=self)
         if self.time and self.time.as_int():
             return self.time.as_int()

    def __repr__(self):
        data = dict(self.data, prefix=self.prefix,
                    sub=self.sub, data=self.config.filename)
        return '<Media %r>' % data


class Player(object):

    pid = os.path.join(tempfile.gettempdir(), 'freeboxtv.pid')
    views = os.path.join(tempfile.gettempdir(), 'freeboxtv')

    player_args = [
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
            '--no-playlist-autostart',
            '--no-sub-autodetect-file',
            ]

    http_args = [
            '--http-src=%s' % views,
            '--extraintf=http',
            '--http-host=:8070',
            ]

    playlist = 'http://mafreebox.freebox.fr/freeboxtv/playlist.m3u'

    def __init__(self):
        if not os.path.isdir(self.views):
            os.makedirs(self.views)
        self.params = config.player
        self.debug = self.params.debug or False
        if 'location' not in self.params:
            self.params.location = os.path.expanduser('~/')
        if 'history_length' not in self.params:
            self.params.history_length = 20

    def start(self, *args):
        if args:
            args = list(args)
            silent = False
        else:
            args = self.player_args
            silent = True
        args = self.http_args + args
        if self.debug:
            stderr = sys.stderr
        else:
            if silent:
                args.insert(0 ,'--intf=dummy')
            stderr = open('/dev/null', 'w')
        args.insert(0, BINARY)
        log.debug('Command: %s', ' '.join(args))
        pid = subprocess.Popen(args, stderr=stderr).pid
        open(self.pid, 'w').write(str(pid))

    @classmethod
    def stop(self):
        if os.path.isfile(self.pid):
            pid = open(self.pid).read()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass

    @property
    def infos(self):
        resp = player.call('info', template='info')
        return Params(json.loads(resp.body))

    def call(self, cmd, *args, **kwargs):
        page = kwargs.get('page', 'tmp.html')
        kwargs.update(cmd=cmd, command=' '.join(args))
        if 'control' not in kwargs:
            kwargs['control'] = Control()
        tmpl = bottle.template(
                    kwargs.get('template', 'cmd'),
                    dict(locals(), **kwargs))
        filename = os.path.join(self.views, page)
        with open(filename, 'w') as fd:
            fd.write(tmpl)
        log.debug(tmpl)
        return self.get_response('/'+page)

    def get_response(self, path_info):
        req = Request.blank(path_info)
        req.environ['SERVER_NAME'] = '127.0.0.1'
        req.environ['SERVER_PORT'] = '8070'
        req.environ['HOST'] = '127.0.0.1:8070'
        resp = req.get_response(proxy_exact_request)
        return resp

    def open_url(self, url, fullscreen=False, **options):
        self.stop()
        cmd = [fullscreen and '-f' or '', '--playlist-autostart', url]
        cmd = [a for a in cmd if a]
        self.start(*cmd)

    def default(self, **options):
        self.open_url(self.playlist, **options)

    @property
    def channels(self):
        page = urllib.urlopen(self.playlist)
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
        for k, v in config.radios.items():
            data = dict(name=k, url=v, raw='%s\n' % v)
            channels[index] = data
            index += 1
        return channels

player = Player()

