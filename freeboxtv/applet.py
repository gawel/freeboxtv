#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import pygtk
pygtk.require('2.0')
import gtk
import gnomeapplet

class Freebox:

    def __init__(self, applet, iid):
        self.applet = applet
        self.iid = iid

def factory(applet, iid):
    Freebox(applet, iid)
    applet.show_all()
    return gtk.TRUE

gnomeapplet.bonobo_factory("OAFIID:GNOME_PysampleApplet_Factory",
    gnomeapplet.Applet.__gtype__,
    "hello", "0", factory)

if len(sys.argv) == 2 and sys.argv[1] == "-t":
    main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    main_window.set_title("Python Applet")
    main_window.connect("destroy", gtk.mainquit)
    app = gnomeapplet.Applet()
    factory(app, None)
    app.reparent(main_window)
    main_window.show_all()
    gtk.main()
    sys.exit()
