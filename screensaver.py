#!/usr/bin/env python

import lights
import random
from gi.repository import GObject

leds = None

try:
	leds = lights.LightArray(16, lights.Apa102Driver())
except:
	leds = lights.LightArray(16, lights.OpenCvDriver())

leds.clear()


def done():
	print("done")

def chaser():
	print "doing chaser..."
	leds.clear()
	animation = lights.SequentialAnimation()
	concurrentTransform = lights.ConcurrentAnimation()
	for i in xrange(leds.ledArraySize):
		concurrentTransform.addAnimation(leds.transformColorTo, i, (0,0,0), 5000)

	r = random.randint(0, 255)
	g = random.randint(0, 255)
	b = random.randint(0, 255)

	print ("chase color: ", r, g, b)

	animation.addAnimation(concurrentTransform.start)
	animation.addAnimation(leds.chase, (r, g, b), 20000, 250)
	animation.addAnimation(concurrentTransform.start)

	animation.start().then(GObject.timeout_add, 1, pickRandomAnimation)

def randomRainbowTransforms():
	print "rainbow..."
	concurrentTransform = lights.ConcurrentAnimation()

	r = random.randint(0, 255)
	g = random.randint(0, 255)
	b = random.randint(0, 255)
	for i in xrange(leds.ledArraySize):
		concurrentTransform.addAnimation(leds.transformColorTo, i, (r,g,b), 5000)
	concurrentTransform.start().then(GObject.timeout_add, 1, randomRainbowTransforms)


def pickRandomAnimation():
	animations = [randomRainbowTransforms, chaser]
	animations[random.randint(0, len(animations)-1)]()


randomRainbowTransforms()

GObject.MainLoop().run()
