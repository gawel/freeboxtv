This package is used to wrap vlc_ and use it with the FreeboxTV_.

.. _vlc: http://www.videolan.org/vlc/
.. _FreeboxTV: http://adsl.free.fr/tv/multiposte/

.. contents::

Requirements
------------

You need vlc_ >= 0.8.6f

Installation
------------

Install freeboxtv with easy_install::

  $ sudo easy_install -U freeboxtv

Troubleshooting
---------------

Some versions of vlc_ require a `--m3u-extvlcopt` option to read `.m3u` files
options. If you need this, you can add a `.freeboxtv` in your `$HOME` and add
this::

  [default]
  options = --m3u-extvlcopt

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

  $ fbxtv france 2 # lauch France 2

Close vlc::

  $ fbxtv -s

Changes
-------

