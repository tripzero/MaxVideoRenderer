#!/usr/bin/env python

from gi.repository import GObject

import sys
import argparse

import videoplayer
import cv2
import numpy as np
import lights
import lightserver
import json

from PyQt5.QtWidgets import QApplication

leds = None
config = None

def colorChanged(r, g, b, id):
	color = (r, g, b)

	colorFormat = config['picture']['colorFormat']

	if colorFormat == 'bgr':
		color = (b, g, r)
	elif colorFormat == 'rbg':
		color = (r, b, g)
	elif colorFormat == 'gbr':
		color = (g, b, r)

	if leds is not None:
		leds.changeColor(id, color)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="maxrenderer", description='minnowboard max dlna renderer with opencv', add_help=True)
	parser.add_argument('--file', help='play file instead', dest="file")
	parser.add_argument('--repeat', action='store_true', help="repeat media", dest='repeat')
	parser.add_argument('--exit', action='store_true', help='exit when playback is complete', dest='exit')
	parser.add_argument('--drivers', action='store_true', help='list drivers and then exit', dest='drivers')

	args = parser.parse_args()

	if args.drivers:
		print(lights.drivers)
		sys.exit()

	app = QApplication(sys.argv)

	with open('config.json') as dataFile:
		config = json.load(dataFile)

	player = videoplayer.Player(config)
	player.colorChanged.connect(colorChanged)

	bottom = config["bottom"]["ledCount"]
	right = config["right"]["ledCount"]
	top = config["top"]["ledCount"]
	left = config["left"]["ledCount"]

	numLeds = bottom + right + top + left

	driver = None
	driverName = config["driver"]["name"]
	if driverName == "Ws2801":
		driver = lights.Ws2801Driver()
	elif driverName == "Apa102":
		freq = config['driver']['freq']
		driver = lights.Apa102Driver(freq)
	elif drivernmae = "WSClient":
		addy = config["driver"]["address"]
		port = config["driver"]["port"]
		driver = lightserver.WSClientDriver(addy, port)
	else:
		driver = lights.OpenCvDriver((bottom, right, top, left))

	leds = lights.LightArray(numLeds, driver)

	player.setNumLeds((bottom, right, top, left))
	player.playbackFinished.connect(leds.clear)

	if args.file is not None:
		player.setMedia(args.file)
		player.repeat = args.repeat
		player.exitOnFinish = args.exit
		player.play()

	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app.exec_()

