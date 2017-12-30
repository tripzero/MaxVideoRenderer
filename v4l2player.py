#!/usr/bin/env python3

import asyncio
import math

import multiprocessing.queues
import multiprocessing

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


class SharedCounter(object):
	""" A synchronized shared counter.
    The locking done by multiprocessing.Value ensures that only a single
    process or thread may read or write the in-memory ctypes object. However,
    in order to do n += 1, Python performs a read followed by a write, so a
    second process may read the old value before the new one is written by the
    first process. The solution is to use a multiprocessing.Lock to guarantee
    the atomicity of the modifications to Value.
    This class comes almost entirely from Eli Bendersky's blog:
    http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/
    """

	def __init__(self, n = 0):
		self.count = multiprocessing.Value('i', n)

	def increment(self, n = 1):
		""" Increment the counter by n (default = 1) """
		with self.count.get_lock():
			self.count.value += n

	@property
	def value(self):
		""" Return the value of the counter """
		return self.count.value


class Queue():
	""" A portable implementation of multiprocessing.Queue.
    Because of multithreading / multiprocessing semantics, Queue.qsize() may
    raise the NotImplementedError exception on Unix platforms like Mac OS X
    where sem_getvalue() is not implemented. This subclass addresses this
    problem by using a synchronized shared counter (initialized to zero) and
    increasing / decreasing its value every time the put() and get() methods
    are called, respectively. This not only prevents NotImplementedError from
    being raised, but also allows us to implement a reliable version of both
    qsize() and empty().
    """

	def __init__(self, *args, **kwargs):
		super(Queue, self).__init__(*args, **kwargs)
		self.m_queue = multiprocessing.Queue()
		self.size = SharedCounter(0)

	def put(self, *args, **kwargs):
		self.size.increment(1)
		self.m_queue.put(*args, **kwargs)

	def get(self, *args, **kwargs):
		self.size.increment(-1)
		return self.m_queue.get(*args, **kwargs)

	def qsize(self):
		""" Reliable implementation of multiprocessing.Queue.qsize() """
		return self.size.value

	def empty(self):
		""" Reliable implementation of multiprocessing.Queue.empty() """
		return not self.qsize()


def run(work_queue, config):

		if not "driver" in config:
			print("No driver specified in config.")
			return

		driver = getDriver(config["driver"]["name"])()

		numLeds = [config["bottom"]["ledCount"], config["right"]["ledCount"], config["top"]["ledCount"], config["left"]["ledCount"]]

		leds = LightArray2(np.sum(numLeds), driver)

		while True:
			#catch up to the latest frame if we are behind
			while work_queue.qsize() > 1:
				toss = work_queue.get()

			frame = work_queue.get()

			bottom = numLeds[0]
			right = numLeds[1]
			top = numLeds[2]
			left = numLeds[3]

			rgbImg = frame

			if config["picture"]["yuv420Convert"]:
				rgbImg = cv2.cvtColor(rgbImg, cv2.COLOR_YUV2RGB_I420)

			height = rgbImg.shape[0]
			width = rgbImg.shape[1]

			i = 0
			yStep = math.floor(height / 8)
			xStep = math.floor(width / 8)

			if right != 0:
				yStep = math.floor(height / (right))
			if bottom != 0:
				xStep = math.floor(width / (bottom))

			#bottom:
			y=height
			x = 0
			for n in range(bottom):
				m = cv2.mean(rgbImg[height - yStep : height, x : x + xStep])
				color = m[:3]
				leds.changeColor(i, color)
				i += 1
				x += xStep

			#right:
			for n in range(right):
				color = cv2.mean(rgbImg[y - yStep : y, width - xStep : width])[:3]
				leds.changeColor(i, color)
				y -= yStep
				i += 1

			#reset steps for top and left
			yStep = math.floor(height / 8)
			xStep = math.floor(width / 8)

			if left != 0:
				yStep = math.floor(height / (left))
			if top != 0:
				xStep = math.floor(width / (top))

			x = width

			#top
			for n in range(top):
				color = cv2.mean(rgbImg[0 : yStep, x - xStep : x])[:3]
				leds.changeColor(i, color)
				x -= xStep
				i += 1

			y = 0

			#left
			for n in range(left):
				color = cv2.mean(rgbImg[y : y + yStep, 0 : xStep])[:3]
				leds.changeColor(i, color)
				i += 1
				y += yStep

			leds.updateNow()
			#cv2.waitKey(1)

class Player:
	def __init__(self, config, test=False):

		self.queue = Queue()
		self.lights = multiprocessing.Process(target=run, args=(self.queue, config))

		self.lights.start()

		p = self.create_pipeline()

		if test:
			p = self.create_test_pipeline()
		
		p.set_state(Gst.State.PLAYING)

		self.bin = p

	def create_pipeline(self, source=None, device="/dev/video0"):
		p = Gst.Bin()

		if source == None:
			source = Gst.ElementFactory.make("v4l2src")

		videoconvert = Gst.ElementFactory.make("videoconvert")

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
		p.add(videoconvert)
		p.add(cvpassthrough)
		p.add(vsink)

		source.link(videoconvert)
		videoconvert.link(cvpassthrough)
		cvpassthrough.link(vsink)

		return p

	def create_test_pipeline(self):
		p = Gst.Bin()


		source = Gst.ElementFactory.make("videotestsrc")

		return self.create_pipeline(source)


	def processFrame(self, frame):
		rgbImg = cv2.pyrDown(frame)
		rgbImg = cv2.pyrDown(rgbImg)
		self.queue.put(rgbImg)


if __name__ == "__main__":
	import argparse
	import json

	parser = argparse.ArgumentParser()
	parser.add_argument('--config', type=str, dest="config_name", default="config.json", help="config")
	parser.add_argument('--test', action='store_true', help='use test source')
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
	
	p = Player(config, args.test)

	asyncio.get_event_loop().run_forever()
