#!/usr/bin/env python

from gi.repository import GObject

import sys
import argparse

import videoplayer
import cv2
import numpy as np
import lights

from PyQt5.QtWidgets import QApplication

leds = None

def colorChanged(r, g, b, id):
	if leds is not None:
		leds.changeColor(id, (r, g, b))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="maxrenderer", description='minnowboard max dlna renderer with opencv', add_help=False)
	parser.add_argument('name', help='name of renderer on the network')
	parser.add_argument('interface', help='network interface to use (ie eth0)')
	parser.add_argument('numLeds', help='number of leds', type=tuple)
	parser.add_argument('--file', help='play file instead', type=string)

	args = parser.parse_args()

	app = QApplication(sys.argv)

	player = videoplayer.Player(args.name, args.interface)
	player.colorChanged.connect(colorChanged)
	try:
		leds = lights.LightArray(args.numLeds, lights.Ws2801Driver())
	except:
		leds = lights.LightArray(args.numLeds, lights.OpenCvDriver())

	player.setNumLeds((11, 28));

	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app.exec_()

