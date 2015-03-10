#!/usr/bin/env python

import cv2
import numpy as np
import datetime
import sys
import concurrent.futures

from gi.repository import GObject, GstVideo, Gst

import gst_hacks as hacks

GObject.threads_init()
Gst.init()


def img_of_frame(frame):
	data = hacks.get_array_video_frame_data_plane(frame.data[0], frame.info.size)
	width = frame.info.width
	height = frame.info.height

	array = np.frombuffer(data, np.uint8)

	img = array.reshape((height, width, 4))

	return img

def img_of_frame_i420(imgBuf, width, height):
	planeSize = width*height
	img=np.zeros((height, width, 3), np.uint8)

	# Luma
	y = np.fromstring(imgBuf[:planeSize], dtype='uint8')
	y.shape = (height, width)
	img[:,:,0] = y

	# Chroma is subsampled, i.e. only available for every 4-th pixel (4:2:0), we need to interpolate
	u = np.fromstring(imgBuf[planeSize:planeSize+planeSize/4], dtype='uint8')
	u.shape = (height/2, width/2)
	img[:,:,1] = cv2.resize(u, (width, height), cv2.INTER_LINEAR) #@UndefinedVariable

	v = np.fromstring(imgBuf[planeSize+planeSize/4: planeSize+planeSize/2], dtype='uint8') #@UndefinedVariable
	v.shape = (height/2, width/2)
	img[:,:,2] = cv2.resize(v, (width, height), cv2.INTER_LINEAR) #@UndefinedVariable

	return cv2.cvtColor(img, cv2.COLOR_YCrCb2RGB)

class OpenCVBaseFilter(GstVideo.VideoFilter):
	""" A basic, buffer forwarding Gstreamer element """

	#here we register our plugin details
	__gstmetadata__ = (
		"OpenCVFilter plugin",
		"Generic",
		"OpenCVFilter is a filter that gives you a nice RGB opencv image to work with",
		"tripzero.kev@gmail.com")

	_srctemplate = Gst.PadTemplate.new('src',
		Gst.PadDirection.SRC,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=RGBx"))

	#sink pad (template): we recieve buffers from our sink pad
	_sinktemplate = Gst.PadTemplate.new('sink',
		Gst.PadDirection.SINK,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=RGBx"))

	#register our pad templates
	__gsttemplates__ = (_srctemplate, _sinktemplate)

	def __init__(self):
		GstVideo.VideoFilter.__init__(self)

class OpenCVFilter(OpenCVBaseFilter):

	callback = None
	passThrough = False

	def __init__(self):
		OpenCVBaseFilter.__init__(self)
		self.set_passthrough(self.passThrough)

	def do_transform_frame(self, inframe, outframe):
		outframe.copy(inframe)
		self.frame = img_of_frame(outframe)
		if self.callback is not None:
			self.callback(self.frame)

		return Gst.FlowReturn.OK

	def do_transform_frame_ip(self, inframe):
		self.frame = img_of_frame(inframe)
		self.callback(self.frame)
		return Gst.FlowReturn.OK

	def do_set_info(self, incaps, in_info, outcaps, out_info):
		return True

	def setCallback(self, cb):
		self.callback = cb

class OpenCVPassthrough(OpenCVBaseFilter):

	_srctemplate = Gst.PadTemplate.new('src',
		Gst.PadDirection.SRC,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=I420"))

	_sinktemplate = Gst.PadTemplate.new('sink',
		Gst.PadDirection.SINK,
		Gst.PadPresence.ALWAYS,
		Gst.Caps.from_string("video/x-raw,format=I420"))

	__gsttemplates__ = (_srctemplate, _sinktemplate)

	executor = None

	def __init__(self):
		OpenCVBaseFilter.__init__(self)
		print "I get no love :("
		self.set_passthrough(True)
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

	def do_transform_frame_ip(self, inframe):
		imgBuf = inframe.buffer.extract_dup(0, inframe.buffer.get_size())
		self.executor.submit(img_of_frame_i420, imgBuf, inframe.info.width, inframe.info.height).add_done_callback(self.checkResult)
		return Gst.FlowReturn.OK

	def do_set_info(self, incaps, in_info, outcaps, out_info):
		return True

	def setCallback(self, cb):
		self.callback = cb

	def checkResult(self, future):
		img = future.result()
		self.callback(img)

def plugin_init_opencv(plugin):
	t = GObject.type_register (OpenCVFilter)
	Gst.Element.register(plugin, "opencvfilter", 0, t)
	return True

def plugin_init_opencvpassthrough(plugin):
	t = GObject.type_register (OpenCVPassthrough)
	Gst.Element.register(plugin, "opencvpassthrough", 0, t)
	return True

Gst.Plugin.register_static(Gst.VERSION_MAJOR, Gst.VERSION_MINOR, "opencvfilter", "opencvfilter filter plugin", plugin_init_opencv, '1', 'LGPL', 'opencvfilter', 'opencvfilter', '')
Gst.Plugin.register_static(Gst.VERSION_MAJOR, Gst.VERSION_MINOR, "opencvpassthrough", "opencvpassthrough filter plugin", plugin_init_opencvpassthrough, '1', 'LGPL', 'opencvpassthrough', 'opencvpassthrough', '')
