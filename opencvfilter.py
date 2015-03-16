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

def img_of_frame_i420(frame):
	width = frame.info.width
	height = frame.info.height
	planeSize = width*height
	imgBuf = hacks.get_array_video_frame_data_plane(frame.data[0], frame.info.size)

	img = np.frombuffer(imgBuf, np.uint8, count=int(width * height * 1.5))
	img.shape = ((height*3/2), width)

	return img

def get_rect_i420(img, x, y, width, height):
	imgHeight, imgWidth = img.shape
	imgHeight = imgHeight / 1.25

	print "height: ", imgHeight

	y = np.array(img[:imgHeight, :imgWidth], np.uint8, copy=False)


	#u = np.array(, np.uint8, copy=False)
	#v = np.array(img[imgHeight/2:imgHeight/2, imgWidth/2:imgWidth/2], np.uint8, copy=False)

	print y
	print img[imgHeight:imgHeight + imgHeight/4]
	#print u
	#print v

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
		self.set_passthrough(True)
		self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

	def do_transform_frame_ip(self, inframe):
		imgBuf = inframe.buffer.extract_dup(0, inframe.buffer.get_size())
		#self.executor.submit(img_of_frame_i420, inframe).add_done_callback(self.checkResult)
		self.callback(img_of_frame_i420(inframe))
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
