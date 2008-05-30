Freebox TV
==========

This package is used to wrap vlc_ and use it with the FreeboxTV_.

.. _vlc: http://www.videolan.org/vlc/
.. _FreeboxTV: http://adsl.free.fr/tv/multiposte/

Installation with easy_install::

  $ easy_install -U freeboxtv

Get channels list::

  $ fbxtv -l

Launch a channel::

  $ fbxtv <channel_id|channel_name>

For example::  

  $ fbxtv nova # launch radio nova

  $ fbxtv france 2 # lauch France 2

Close vlc::

  $ fbxtv -s

Note for Mac OSX
----------------

You need this on Mac OSX::

  cat > vlc << EOF
  #!/bin/bash
  exec /Applications/VLC.app/Contents/MacOS/VLC "\$@"
  EOF
  sudo chown root:wheel vlc
  sudo chmod +x vlc
  sudo mv vlc /usr/bin/vlc

