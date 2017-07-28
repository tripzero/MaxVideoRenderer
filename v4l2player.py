#!/usr/bin/env python3

import asyncio

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GstVideo

GObject.threads_init()
Gst.init(None)

import opencvfilter.opencvfilter


class Player:
	def __init__(self):
		p = Gst.Bin('happybin')

		source = Gst.ElementFactory.make("v4l2src")
		cvpassthrough = Gst.ElementFactory.make("opencvpassthrough")
		vsink = Gst.ElementFactory.make("vaapisink")
		vsink.set_property('fullscreen', True)

		p.add(source)
		p.add(cvpassthrough)
		p.add(vsink)

		source.link(cvpassthrough)
		cvpassthrough.link(vsink)

		p.set_state(Gst.State.PLAYING)

		self.bin = p


if __name__ == "__main__":

	p = Player()

	asyncio.get_event_loop().run_forever()
