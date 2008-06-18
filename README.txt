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

