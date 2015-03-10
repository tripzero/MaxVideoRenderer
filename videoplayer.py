#!/usr/bin/env python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GstVideo, RygelRendererGst

import sys
import cv2
import numpy
import concurrent.futures

import opencvfilter

GObject.threads_init()
Gst.init(None)

def get_avg_pixel(img):
	averagePixelValue = cv2.mean(img)
	return averagePixelValue[0], averagePixelValue[1], averagePixelValue[2]

class FrameAnalyser:

	numthreads = GObject.property(type=int, default=2)
	everyNthFrame = GObject.property(type=int, default=10)

	frameCount = 0
	executor = None

	callback = None

	def __init__(self):
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

	def pool(self, frame):
		self.executor.submit(self.work, frame).add_done_callback(self.checkResult)

	def do_set_info(self, incaps, in_info, outcaps, out_info):
		return True

	def work(self, frame):
		return get_avg_pixel(frame)

	def checkResult(self, future):
		red, green, blue = future.result()
		self.callback(red, green, blue)

class Player:

	colorCallback = None
	renderer = None

	def __init__(self, name, iface):
		self.analyser = FrameAnalyser()

		self.renderer = RygelRendererGst.PlaybinRenderer.new(name)

		self.renderer.add_interface(iface)
		analyserQueue = Gst.ElementFactory.make("queue", "analyserqueue")
		self.newElement = Gst.ElementFactory.make("opencvpassthrough")
		self.newElement.setCallback(self.analyser.pool)

		vsink  = Gst.ElementFactory.make("vaapisink")

		vsink.set_property('fullscreen', True)
		# create the pipeline

		p = Gst.Bin('happybin')

		p.add(analyserQueue)
		p.add(self.newElement)
		p.add(vsink)

		analyserQueue.link(self.newElement)
		self.newElement.link(vsink)

		p.add_pad(Gst.GhostPad.new('sink', analyserQueue.get_static_pad('sink')))

		self.playbin = self.renderer.get_playbin()
		self.playbin.set_property('video-sink', p)

	def play(self):
		self.playbin.set_state(Gst.State.PLAYING)

	def pause(self):
		self.playbin.set_state(Gst.State.PAUSED)

	def stop(self):
		self.playbin.set_state(Gst.State.NULL)

	def setMedia(self, uri):
		self.playbin.set_property('uri', uri)

	def setColorChangedCallback(self, cb):
		self.analyser.callback = cb







