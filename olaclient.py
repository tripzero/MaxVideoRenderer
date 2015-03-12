#!/usr/bin/env python

from gi.repository import GLib
from ola import OlaClient

olaClient = OlaClient.OlaClient()

olaSocket = olaClient.GetSocket()

def onReadable(source, condition):
	olaClient.SocketReady()

GLib.io_add_watch(olaSocket, GLib.PRIORITY_DEFAULT, GLib.IO_IN, onReadable)
