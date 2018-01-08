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

class LedController:
	def __init__(self, config):

		self.config = config

		if not "driver" in config:
			print("No driver specified in config.")
			return

		def get_with_default(dictionary, key, default=0):
			if not key in dictionary:
				return default

			return dictionary[key]

		driver_name = config["driver"]["name"]
		driver_options = get_with_default(config['driver'], 'options', {})
		
		print("using {} with options:".format(driver_name))
		print(driver_options)
		
		driver = getDriver(driver_name)(**driver_options)

		numLeds = [config["bottom"]["ledCount"], config["right"]["ledCount"], config["top"]["ledCount"], config["left"]["ledCount"]]
		self.offsets = [get_with_default(config["bottom"],"offset"),
				   get_with_default(config["right"],"offset"),
				   get_with_default(config["top"],"offset"),
				   get_with_default(config["left"],"offset")]

		self.leds = LightArray2(np.sum(numLeds), driver)

		self.bottom = numLeds[0]
		self.right = numLeds[1]
		self.top = numLeds[2]
		self.left = numLeds[3]

	def show_leds_resize(self, frame):
		if self.config["picture"]["yuv420Convert"]:
			rgbImg = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)

		else:
			rgbImg = frame

		rgbImg = cv2.resize(rgbImg, (np.max([self.top, self.bottom]), np.max([self.left, self.right])))

		height = rgbImg.shape[0] - 1
		width = rgbImg.shape[1] - 1
		led_index = 0

		#bottom:
		offset = self.offsets[0]
		for i in range(self.bottom):
			color = rgbImg[height-offset, i]
			self.leds.changeColor(led_index, color)
			led_index += 1

		offset = self.offsets[1]
		for i in range(self.right):
			color = rgbImg[height - i, width - offset]
			self.leds.changeColor(led_index, color)
			led_index += 1

		offset = self.offsets[2]
		for i in range(self.top):
			color = rgbImg[offset, width - i]
			self.leds.changeColor(led_index, color)
			led_index += 1

		offset = self.offsets[3]
		for i in range(self.left):
			color = rgbImg[i, offset]
			self.leds.changeColor(led_index, color)
			led_index += 1


		self.leds.updateNow()

	def show_leds(self, frame):

		rgbImg = frame

		#cv2.imshow("frame", frame)
		#cv2.waitKey(1)

		if self.config["picture"]["yuv420Convert"]:
			rgbImg = cv2.cvtColor(rgbImg, cv2.COLOR_YUV2RGB_I420)

		height = rgbImg.shape[0]
		width = rgbImg.shape[1]

		i = 0
		yStep = math.floor(height / 8)
		xStep = math.floor(width / 8)

		if self.right != 0:
			yStep = math.floor(height / (self.right))
		if self.bottom != 0:
			xStep = math.floor(width / (self.bottom))

		#bottom:
		y=height
		x = 0
		offset = self.offsets[0]
		for n in range(self.bottom):
			m = cv2.mean(rgbImg[height - yStep - offset : height - offset, x : x + xStep])
			color = m[:3]
			self.leds.changeColor(i, color)
			i += 1
			x += xStep

		#right:
		offset = self.offsets[1]
		for n in range(self.right):
			color = cv2.mean(rgbImg[y - yStep : y, width - xStep - offset: width - offset])[:3]
			self.leds.changeColor(i, color)
			y -= yStep
			i += 1

		#reset steps for top and left
		yStep = math.floor(height / 8)
		xStep = math.floor(width / 8)

		if self.left != 0:
			yStep = math.floor(height / (self.left))
		if self.top != 0:
			xStep = math.floor(width / (self.top))

		x = width

		#top
		offset = self.offsets[2]
		for n in range(self.top):
			color = cv2.mean(rgbImg[0 + offset : yStep + offset, x - xStep : x])[:3]
			self.leds.changeColor(i, color)
			x -= xStep
			i += 1

		y = 0

		#left
		offset = self.offsets[3]
		for n in range(self.left):
			color = cv2.mean(rgbImg[y : y + yStep, 0 + offset : xStep + offset])[:3]
			self.leds.changeColor(i, color)
			i += 1
			y += yStep

		self.leds.updateNow()


def run(work_queue, config):
		leds = LedController(config)

		while True:
			#catch up to the latest frame if we are behind
			while work_queue.qsize() > 1:
				toss = work_queue.get()

			frame = work_queue.get()

			leds.show_leds(frame)

class Player:
	def __init__(self, config, test=False, rt_yield=None, use_fpssink = False):

		#self.led_controller = LedController(config)
		self.rt_yield = rt_yield
		self.use_fpssink = use_fpssink
		self.light_frame_disp = False

		self.queue = Queue()
		self.lights = multiprocessing.Process(target=run, args=(self.queue, config))

		self.lights.start()

		p = self.create_pipeline()

		if test:
			p = self.create_test_pipeline()
		
		p.set_state(Gst.State.PLAYING)

		self.bin = p

	def handoff_callback(self, sink, buffer, pad):
		if self.rt_yield:
			self.rt_yield()


	def create_pipeline(self, source=None, device="/dev/video0"):
		p = Gst.Bin()

		if source == None:
			source = Gst.ElementFactory.make("v4l2src")
			source.set_property('device', device)

		camera1caps = Gst.Caps.from_string("video/x-raw, width=1920,height=1080,framerate=60/1")
		camerafilter = Gst.ElementFactory.make("capsfilter", "filter1")
		camerafilter.set_property("caps", camera1caps)

		videoconvert = Gst.ElementFactory.make("videoconvert")
		videoconvert2 = Gst.ElementFactory.make("videoconvert")

		cvpassthrough = Gst.ElementFactory.make("opencvpassthrough")

		if not cvpassthrough:
			print("Failed to load opencvpassthrough")
			return

		vsink = Gst.ElementFactory.make("vaapisink")

		if not vsink:
			print("Failed to load vaapisink.")
			return

		vsink.set_property('fullscreen', True)
		vsink.connect('handoff', self.handoff_callback)

		if self.use_fpssink:
			fpssink = Gst.ElementFactory.make('fpsdisplaysink')
			fpssink.set_property("video-sink", vsink)
			vsink = fpssink

		cvpassthrough.setCallback(self.processFrame)

		p.add(source)
		p.add(camerafilter)
		p.add(videoconvert)
		p.add(cvpassthrough)
		p.add(videoconvert2)
		p.add(vsink)

		source.link(camerafilter)
		camerafilter.link(videoconvert)
		videoconvert.link(cvpassthrough)
		cvpassthrough.link(videoconvert2)
		videoconvert2.link(vsink)

		return p

	def create_test_pipeline(self):
		p = Gst.Bin()

		source = Gst.ElementFactory.make("videotestsrc")

		return self.create_pipeline(source)


	def processFrame(self, frame):

		if self.queue.qsize() <= 1:
			height, width, depth = frame.shape
			frame = cv2.pyrDown(frame, ((height+1)/64, (width+1)/64))
			self.queue.put(frame)


if __name__ == "__main__":
	import argparse
	import json

	parser = argparse.ArgumentParser()
	parser.add_argument('--config', type=str, dest="config_name", default="config.json", help="config")
	parser.add_argument('--test', action='store_true', help='use test source')
	parser.add_argument('--rt', action="store_true", help='user realtime scheddl')
	parser.add_argument('--disp_fps', action="store_true", help='display fps counter')
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

	framerate = 60
	rt_yield = None

	if args.rt:
		import scheddl

		dl_args = (
		    (int(1000/framerate) - 1) * 1000 * 1000, # runtime in nanoseconds
		    int(1000/framerate) * 1000 * 1000, # deadline in nanoseconds
		    int(1000/framerate) * 1000 * 1000  # time period in nanoseconds
		)

		scheddl.set_deadline(*dl_args, scheddl.RESET_ON_FORK)
		rt_yield = scheddl.sched_yield

	p = Player(config, args.test, rt_yield, args.disp_fps)

	asyncio.get_event_loop().run_forever()
