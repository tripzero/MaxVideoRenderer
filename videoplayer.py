#!/usr/bin/env python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GstVideo, RygelRendererGst

import sys
import cv2
import numpy
import Queue

from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal

import opencvfilter.opencvfilter

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
	test = False

	def __init__(self, workQueue, config):
		super(FrameAnalyser, self).__init__()
		self.workQueue = workQueue
		self.config = config


	def run(self):
		while True:
			#catch up to the latest frame if we are behind
			while self.workQueue.qsize() > 1:
				self.workQueue.get()
			frame = self.workQueue.get()

			bottom = self.numLeds[0]
			right = self.numLeds[1]
			top = self.numLeds[2]
			left = self.numLeds[3]
			#rgbImg = frame
			rgbImg = cv2.pyrDown(frame)
			rgbImg = cv2.pyrDown(rgbImg)

			if self.config["picture"]["yuv420Convert"]:
				rgbImg = cv2.cvtColor(rgbImg, cv2.COLOR_YUV2BGR_I420)

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
			for n in xrange(bottom):
				color = get_avg_pixel(rgbImg[height - yStep : height, x : x + xStep])
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				i += 1
				x += xStep

			#right:
			for n in xrange(right):
				color = get_avg_pixel(rgbImg[y - yStep : y, width - xStep : width])
				self.hasResults.result.emit(color[0], color[1], color[2], i)
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
			for n in xrange(top):
				color = get_avg_pixel(rgbImg[0 : yStep, x - xStep : x])
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				x -= xStep
				i += 1

			y = 0

			#left
			for n in xrange(left):
				color = get_avg_pixel(rgbImg[y : y + yStep, 0 : xStep])
				self.hasResults.result.emit(color[0], color[1], color[2], i)
				i += 1
				y += yStep


	def checkResult(self, future):
		color, id = future.result()
		self.callback(color, id)

class Player(QObject):

	colorCallback = None
	renderer = None

	colorChanged = pyqtSignal(float, float, float, int)
	playbackFinished = pyqtSignal()

	repeat = False
	numLeds = 0
	exitOnFinish = False

	def __init__(self, config):
		QObject.__init__(self)
		self.config = config
		self.workQueue = Queue.Queue()
		self.analyser = FrameAnalyser(self.workQueue, config)
		self.analyser.hasResults.result.connect(self.colorChanged)
		self.pool = QThreadPool()
		self.pool.setMaxThreadCount(4)
		self.pool.start(self.analyser)

		self.renderer = RygelRendererGst.PlaybinRenderer.new(config['dlnaRenderer']['name'])

		self.renderer.add_interface(config['dlnaRenderer']['interface'])
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
		self.playbackFinished.emit()
		if self.exitOnFinish:
			sys.exit()
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

	def __del__(self):
		self.pool.waitForDone()

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







