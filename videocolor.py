#!/usr/bin/env python

from gi.repository import GLib
from gi.repository import GObject

import sys

import videoplayer

def colorChanged(r, g, b):
	pass

print("Hello world!")

player = videoplayer.Player()
player.setColorChangedCallback(colorChanged)

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

GLib.MainLoop().run()

