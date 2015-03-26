#!/usr/bin/env python

import lights
import random
from gi.repository import GObject

leds = None

try:
	leds = lights.LightArray(28, lights.Ws2801Driver())
except:
	leds = lights.LightArray(28, lights.OpenCvDriver())

leds.clear()


def done():
	print("done")

def randomRainbowTransforms():
	concurrentTransform = lights.ConcurrentAnimation()

	for i in xrange(leds.ledArraySize):
		r = random.randint(0, 255)
		g = random.randint(0, 255)
		b = random.randint(0, 255)
		concurrentTransform.addAnimation(leds.transformColorTo, i, (r,g,b), 5000)
	concurrentTransform.start().then(GObject.timeout_add, 1, randomRainbowTransforms)

randomRainbowTransforms()

GObject.MainLoop().run()
