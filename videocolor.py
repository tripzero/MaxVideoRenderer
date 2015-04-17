#!/usr/bin/env python

from gi.repository import GObject

import sys
import argparse

import videoplayer
import cv2
import numpy as np
import lights
import json

from PyQt5.QtWidgets import QApplication

leds = None

def colorChanged(r, g, b, id):
	if leds is not None:
		leds.changeColor(id, (r, g, b))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="maxrenderer", description='minnowboard max dlna renderer with opencv', add_help=False)
	parser.add_argument('--file', help='play file instead', dest="file")
	parser.add_argument('--repeat', action='store_true', help="repeat media", dest='repeat')
	parser.add_argument('--exit', action='store_true', help='exit when playback is complete', dest='exit')

	args = parser.parse_args()

	app = QApplication(sys.argv)

	config = None

	with open('config.json') as dataFile:
		config = json.load(dataFile)

	player = videoplayer.Player(config["dlnaRenderer"]["name"], config["dlnaRenderer"]["interface"])
	player.colorChanged.connect(colorChanged)

	bottom = config["bottom"]["ledCount"]
	right = config["right"]["ledCount"]
	top = config["top"]["ledCount"]
	left = config["left"]["ledCount"]

	numLeds = bottom + right + top + left

	driver = None
	driverName = config["driver"]
	if driverName == "Ws2801":
		leds = lights.LightArray(numLeds, lights.Ws2801Driver())
	elif driverName == "Apa102":
		leds = lights.LightArray(numLeds, lights.Apa102Driver())
	else:
		leds = lights.LightArray(numLeds, lights.OpenCvDriver())

	player.setNumLeds((bottom, right, top, left));

	if args.file is not None:
		player.setMedia(args.file)
		player.repeat = args.repeat
		player.exitOnFinish = args.exit
		player.play()

	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app.exec_()

