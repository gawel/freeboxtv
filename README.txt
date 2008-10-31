This package is used to wrap vlc_ and use it with the FreeboxTV_.

.. _vlc: http://www.videolan.org/vlc/
.. _FreeboxTV: http://adsl.free.fr/tv/multiposte/

.. contents::

Requirements
------------

You need vlc_

Installation
------------

Install freeboxtv with easy_install::

  $ sudo easy_install -U freeboxtv

Troubleshooting
---------------

Some older versions of vlc_ require a `--m3u-extvlcopt` option to read `.m3u`
files options. If you need this, you can add a `.freeboxtv` in your `$HOME` and
add this::

  [default]
  options = --m3u-extvlcopt

If you still having problems, run::

  $ fbxtv -d

And send the traceback at `gael at gawel dot org`.  

Usage
-----

Get channels list::

  $ fbxtv -l

Launch the full playlist::

  $ fbxtv

Launch a channel::

  $ fbxtv <channel_id|channel_name>

For example::  

  $ fbxtv nova # launch radio nova

  $ fbxtv france 2 # launch France 2

Close vlc::

  $ fbxtv -s

Changes
-------

