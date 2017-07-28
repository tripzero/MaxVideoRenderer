#!/usr/bin/env python3

import asyncio
from multiprocessing import Queue, Process
from photons import LightArray2, getDriver
import cv2
import numpy as np

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GstVideo

GObject.threads_init()
Gst.init(None)

import opencvfilter.opencvfilter

def run(workQueue, config):

		if not "driver" in config:
			print("No driver specified in config.")
			return

		driver = getDriver(config["driver"]["name"])

		numLeds = [config["bottom"]["ledCount"], config["right"]["ledCount"], config["top"]["ledCount"], config["left"]["ledCount"]]

		leds = LightArray2(np.sum(numLeds), driver)

		while True:
			#catch up to the latest frame if we are behind
			frame = workQueue.get()

			bottom = numLeds[0]
			right = numLeds[1]
			top = numLeds[2]
			left = numLeds[3]

			#rgbImg = frame
			rgbImg = cv2.pyrDown(frame)
			rgbImg = cv2.pyrDown(rgbImg)

			if config["picture"]["yuv420Convert"]:
				rgbImg = cv2.cvtColor(rgbImg, cv2.COLOR_YUV2RGB_I420)

			height = rgbImg.shape[0]
			width = rgbImg.shape[1]

			i = 0
			yStep = height / 8
			xStep = width / 8

			if right != 0:
				yStep = height / (right)
			if bottom != 0:
				xStep = width / (bottom)

			#bottom:
			y=height
			x = 0
			for n in range(bottom):
				color = cv2.mean(rgbImg[height - yStep : height, x : x + xStep])
				leds.changeColor(i, color)
				i += 1
				x += xStep

			#right:
			for n in range(right):
				color = cv2.mean(rgbImg[y - yStep : y, width - xStep : width])
				leds.changeColor(i, color)
				y -= yStep
				i += 1

			#reset steps for top and left
			yStep = height / 8
			xStep = width / 8

			if left != 0:
				yStep = height / (left)
			if top != 0:
				xStep = width / (top)

			x = width

			#top
			for n in range(top):
				color = cv2.mean(rgbImg[0 : yStep, x - xStep : x])
				leds.changeColor(i, color)
				x -= xStep
				i += 1

			y = 0

			#left
			for n in range(left):
				color = cv2.mean(rgbImg[y : y + yStep, 0 : xStep])
				leds.changeColor(i, color)
				i += 1
				y += yStep

class Player:
	def __init__(self, config):

		self.queue = Queue()
		self.lights = Process(target=run, args=(self.queue, config))

		self.lights.start()

		p = Gst.Bin()


		source = Gst.ElementFactory.make("v4l2src")
		cvpassthrough = Gst.ElementFactory.make("opencvpassthrough")

		if not cvpassthrough:
			print("Failed to load opencvpassthrough")
			return

		vsink = Gst.ElementFactory.make("vaapisink")

		if not vsink:
			print("Failed to load vaapisink.")
			return

		vsink.set_property('fullscreen', True)

		cvpassthrough.setCallback(self.processFrame)

		p.add(source)
		p.add(cvpassthrough)
		p.add(vsink)

		source.link(cvpassthrough)
		cvpassthrough.link(vsink)

		p.set_state(Gst.State.PLAYING)

		self.bin = p

	def processFrame(self, frame):
		self.queue.put(frame)


if __name__ == "__main__":
	import argparse
	import json

	parser = argparse.ArgumentParser()
	parser.add_argument('--config', type=str, dest="config_name", default="config.json", help="config")
	args, unknown = parser.parse_known_args()

	config = None

	try:
		with open(args.config_name,'r') as f:
			config = json.loads(f.read())
	except:
		print("config not loaded")
		import sys, traceback
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
		traceback.print_exception(exc_type, exc_value, exc_traceback,
                		          limit=6, file=sys.stdout)
	
	p = Player(config)

	asyncio.get_event_loop().run_forever()