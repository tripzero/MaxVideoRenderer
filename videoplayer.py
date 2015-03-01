#!/usr/bin/env python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GstVideo, RygelRendererGst

import sys
import cv2
import numpy
from Queue import *
from threading import *

GObject.threads_init()
Gst.init(None)

def img_of_buf(buf, caps):
	data = buf.extract_dup(0, buf.get_size())

	if buf is None:
		return None
	struct = caps[0]

	width = struct['width']
	height = struct['height']

	array = numpy.frombuffer(data, dtype=numpy.uint8)

	img = array.reshape((height, width, 3))

	return img

def img_of_frame(frame):
	data = frame.buffer.extract_dup(0, frame.buffer.get_size())

	width = frame.info.width
	height = frame.info.height

	array = numpy.fromstring(data, numpy.uint8)

	img = array.reshape((height, width, 3))

	return img

def img_of_frame_i420(imgBuf, width, height):
	planeSize = width*height
	img=numpy.zeros((height, width, 3), numpy.uint8)

	# Luma
	y = numpy.fromstring(imgBuf[:planeSize], dtype='uint8')
	y.shape = (height, width)
	img[:,:,0] = y

	# Chroma is subsampled, i.e. only available for every 4-th pixel (4:2:0), we need to interpolate
	u = numpy.fromstring(imgBuf[planeSize:planeSize+planeSize/4], dtype='uint8')
	u.shape = (height/2, width/2)
	img[:,:,1] = cv2.resize(u, (width, height), cv2.INTER_LINEAR) #@UndefinedVariable

	v = numpy.fromstring(imgBuf[planeSize+planeSize/4: planeSize+planeSize/2], dtype='uint8') #@UndefinedVariable
	v.shape = (height/2, width/2)
	img[:,:,2] = cv2.resize(v, (width, height), cv2.INTER_LINEAR) #@UndefinedVariable

	return cv2.cvtColor(img, cv2.COLOR_YCrCb2RGB)


def get_avg_pixel(img):
	height, width, layers = img.shape

	#img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

	averagePixelValue = cv2.mean(img)

	#rect = cv2.rectangle(img, (0,0), (width, height), averagePixelValue, -1)

	#cv2.imshow('color', rect)

	return averagePixelValue

class NewElement(GstVideo.VideoFilter):
	""" A basic, buffer forwarding Gstreamer element """

	#here we register our plugin details
	__gstmetadata__ = (
		"NewElement plugin",
		"Generic",
		"Description is really cool",
		"Contact")

	__gsignals__ = { 'avg_color' : (GObject.SIGNAL_RUN_FIRST, None, (int, int, int,)) }

	_srctemplate = Gst.PadTemplate.new('src',
		Gst.PadDirection.SRC,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=I420"))

	#sink pad (template): we recieve buffers from our sink pad
	_sinktemplate = Gst.PadTemplate.new('sink',
		Gst.PadDirection.SINK,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=I420"))

	#register our pad templates
	__gsttemplates__ = (_srctemplate, _sinktemplate)

	q = Queue()
	rq = Queue()
	frameCount = 0

	def __init__(self):
		GstVideo.VideoFilter.__init__(self)
		self.set_passthrough(True)
		self.t = Thread(target=self.worker)
		self.t.daemon = True
		self.t.start()
		GObject.idle_add(self.checkResult)

	def do_transform_frame_ip(self, inframe):
		self.frameCount += 1
		if self.frameCount == 10:
			self.frameCount = 0
			imgBuf = inframe.buffer.extract_dup(0, inframe.buffer.get_size())
			self.q.put((imgBuf, inframe.info.width, inframe.info.height))
		return Gst.FlowReturn.OK

	def do_set_info(self, incaps, in_info, outcaps, out_info):
		return True

	def worker(self):
		while True:
			frame, width, height = self.q.get()
			self.rq.put(get_avg_pixel(img_of_frame_i420(frame, width, height)))

	def checkResult(self):
		if not self.rq.empty():
			color = self.rq.get()
			self.emit('avg_color', color[0], color[1], color[2])
		return True


def plugin_init(plugin):
	t = GObject.type_register (NewElement)
	Gst.Element.register(plugin, "newelement", 0, t)
	return True

Gst.Plugin.register_static(Gst.VERSION_MAJOR, Gst.VERSION_MINOR, "newelement", "newelement filter plugin", plugin_init, '12.06', 'LGPL', 'newelement1', 'newelement2', '')

class Player:

	colorCallback = None
	renderer = None

	def __init__(self):
		self.renderer = RygelRendererGst.PlaybinRenderer.new("Awesome Renderer")

		self.renderer.add_interface("wlan0")

		vsource = Gst.ElementFactory.make('videotestsrc')
		self.newElement = Gst.ElementFactory.make("newelement")

		self.newElement.connect('avg_color', self._privateColorHandler)

		vconvert1 = Gst.ElementFactory.make("videoconvert", 'vconvert1')
		#filter2 = Gst.ElementFactory.make("capsfilter", 'filter2')
		#filter2.set_property('caps', Gst.Caps.from_string("video/x-raw,format=I420"))
		#vconvert2 = Gst.ElementFactory.make("videoconvert", 'vconvert2')
		#use vaapisink when it works:
		vsink  = Gst.ElementFactory.make("vaapisink")

		vsink.set_property('fullscreen', True)
		# create the pipeline

		p = Gst.Bin('happybin')
		p.add(self.newElement)
		#p.add(vconvert1)
		#p.add(filter2)
		#p.add(vconvert2)
		p.add(vsink)

		#self.newElement.link(vconvert1)
		#vconvert1.link(filter2)
		#filter2.link(vconvert2)
		#vconvert2.link(vsink)
		self.newElement.link(vsink)

		p.add_pad(Gst.GhostPad.new('sink', self.newElement.get_static_pad('sink')))

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
		self.colorCallback = cb

	def _privateColorHandler(self, r, g, b, data):
		if self.colorCallback is not None:
			self.colorCallback(r, g, b)





