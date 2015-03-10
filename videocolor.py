#!/usr/bin/env python

from gi.repository import GObject

import sys
import argparse

import videoplayer
import iodclient

def colorChanged(r, g, b):
	#print("i can has colors: ", r, g, b)
	pass

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="maxrenderer", description='minnowboard max dlna renderer with opencv', add_help=False)
	parser.add_argument('name', help='name of renderer on the network')
	parser.add_argument('interface', help='network interface to use (ie eth0)')

	args = parser.parse_args()


	player = videoplayer.Player(args.name, args.interface)
	player.setColorChangedCallback(colorChanged)
	player.setMedia('file:///home/tripzero/Videos/Visual_Dreams_720.mp4')
	player.play()

	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	GObject.MainLoop().run()

