#/usr/bin/env python

import iodclient
import numpy as np
import dbus
from gi.repository import GObject

class Chase:
	steps = 0
	step = 0
	led = 0
	color = (0,0,0)
	forward = True

	def __init__(self, color, steps):
		self.color = color
		self.steps = steps

class TransformToColor:
	targetColor = [0,0,0]
	led = 0
	def __init__(self, led, targetColor):
		self.led = led
		self.targetColor = targetColor

class Ws2801:
	ledArraySize = 0
	ledsData = None
	spiDev = None

	def __init__(self, ledArraySize):
		self.ledArraySize = ledArraySize
		self.ledsData = np.zeros((ledArraySize+1, 3), np.uint8)
		client = iodclient.IodClient()
		self.spiDev = client.spi[0]

	def clear(self):
		self.ledsData[:] = (0,0,0)
		self.update()

	def update(self):
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		self.update()

	def chase(self, color, time, delay):
		steps = time / delay
		c = Chase(color, steps)
		GObject.timeout_add(delay, self._doChase, c)

	def _doChase(self, c):
		if c.step >= c.steps:
			return False
		if c.led >= self.ledArraySize:
			c.forward = False
		if c.led <= 0:
			c.forward = True

		if c.forward == True:
			c.led += 1
		else:
			c.led -= 1

		self.clear()
		self.changeColor(c.led, c.color)
		c.step += 1

		return True

	def transformColorTo(self, led, color, time):
		prevColor = self.ledsData[led]
		steps = [color[0] - prevColor[0], color[1] - prevColor[1], color[2] - prevColor[2]]
		stepsAbs = [abs(steps[0]), abs(steps[1]), abs(steps[2])]
		delay = time / max(stepsAbs)
		t = TransformToColor(led, color)
		GObject.timeout_add(delay, self._doTransformColorTo, t)

	def _doTransformColorTo(self, transform):
		stillStepping = False
		color = self.ledsData[transform.led]
		for i in xrange(3):
			if color[i] < transform.targetColor[i]:
				color[i] += 1
				stillStepping = True
			elif color[i] > transform.steps[i]:
				color[i] -= 1
				stillStepping = True
		self.ledsData[transform.led] = color
		self.update()
		return stillStepping









