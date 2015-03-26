#!/usr/bin/env python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GstVideo, RygelRendererGst

import sys
import cv2
import numpy
import Queue

from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal

import opencvfilter

GObject.threads_init()
Gst.init(None)

def get_avg_pixel(img):
	return cv2.mean(img)

class FrameAnalyserSignals(QObject):
	result = pyqtSignal(float, float, float, int)

class FrameAnalyser(QRunnable):
	hasResults = FrameAnalyserSignals()
	numLeds = 0
	testFrame = None

	def __init__(self, workQueue):
		super(FrameAnalyser, self).__init__()
		self.workQueue = workQueue

	def run(self):
		while True:
			while self.workQueue.qsize() > 1:
				self.workQueue.get()
			#catch up to the latest frame if we are behind
			frame = self.workQueue.get()
			#convert i420 to RGB
			dheight = self.numLeds[0]
			dwidth = self.numLeds[1]

			rgbImg = cv2.cvtColor(frame, cv2.COLOR_YUV2RGB_I420)
			#rgbImg = cv2.pyrDown(rgbImg)

			#cv2.imshow("rgbimg downscaled: ", rgbImg)

			height = rgbImg.shape[0]
			width = rgbImg.shape[1]

			if self.testFrame == None:
				self.testFrame = numpy.zeros((height, width, 3), numpy.uint8)

			i = 0
			yStep = height / dheight
			xStep = width / dwidth

			y=height-1
			x = 1
			while x < width:
				color = get_avg_pixel(rgbImg[height - yStep : height, x : x + xStep])
				self.testFrame[height - yStep : height, x : x + xStep] = color[:3]
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				i += 1
				x += xStep

			while y >= 0:
				color = get_avg_pixel(rgbImg[y : y + yStep, width - xStep : width])
				self.testFrame[y : y + yStep, width - xStep : width] = color[:3]
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				y -= yStep
				i += 1

			while x >= 0:
				color = get_avg_pixel(rgbImg[0 : yStep, x - xStep : x])
				self.testFrame[0 : yStep, x - xStep : x] = color[:3]
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				x -= xStep
				i += 1

			while y < height:
				color = get_avg_pixel(rgbImg[y : y + yStep, 0 : xStep])
				self.testFrame[y : y + yStep, 0 : xStep] = color[:3]
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				i += 1
				y += yStep

			cv2.imshow("test", self.testFrame)
			'''for i in xrange(self.numLeds - 1):
				x = width / self.numLeds * i
				y = height / 2 - 20
				color = get_avg_pixel(rgbImg[y : y + 20, x : x + 20])
				self.hasResults.result.emit(color[0], color[1], color[2], i)
			'''


	def checkResult(self, future):
		color, id = future.result()
		self.callback(color, id)

class Player(QObject):

	colorCallback = None
	renderer = None

	colorChanged = pyqtSignal(float, float, float, int)
	repeat = False
	numLeds = 0
	def __init__(self, name, iface):
		QObject.__init__(self)
		self.workQueue = Queue.Queue()
		self.analyser = FrameAnalyser(self.workQueue)
		self.analyser.hasResults.result.connect(self.colorChanged)
		self.pool = QThreadPool()
		self.pool.setMaxThreadCount(4)
		self.pool.start(self.analyser)

		self.renderer = RygelRendererGst.PlaybinRenderer.new(name)

		self.renderer.add_interface(iface)
		analyserQueue = Gst.ElementFactory.make("queue", "analyserqueue")
		self.newElement = Gst.ElementFactory.make("opencvpassthrough")
		self.newElement.setCallback(self.addQueue)

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
		self.bus = self.playbin.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message::eos", self.on_finish)

	def __del__(self):
		self.pool.waitForDone()
		self.stop()

	def on_finish(self, bus, message):
		print "stream finished"
		self.stop()
		if self.repeat == True:
			print "replaying!"
			if not self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH , 0):
				print "Error seeking back to the beginning"
			GObject.timeout_add(1000, self.play)
		else:
			print "not replaying.  repeat is ", self.repeat

	def addQueue(self, frame):
		self.workQueue.put(frame)

	def play(self):
		self.playbin.set_state(Gst.State.PLAYING)

	def pause(self):
		self.playbin.set_state(Gst.State.PAUSED)

	def stop(self):
		self.playbin.set_state(Gst.State.NULL)

	def setMedia(self, uri):
		self.uri = uri
		self.playbin.set_property('uri', uri)

	def setNumLeds(self, numLeds):
		self.numLeds = numLeds
		self.analyser.numLeds = numLeds






