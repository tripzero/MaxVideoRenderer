#!/usr/bin/env python

import mraa
import lights
import random
from gi.repository import GObject

print mraa.getVersion()

leds = lights.Ws2801(28)
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
