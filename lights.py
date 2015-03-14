#/usr/bin/env python

import iodclient
import numpy as np
import dbus
import GObject

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
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def chase(self, color, time, delay):
		steps = time / delay
		led = 0
		step = 0
		forward = True
		GObject.timeout_add(delay, self._doChase, led, color, step, stepsn forward)

	def _doChase(self, led, color, step, steps, forward):
		if step >= steps:
			return False
		if led >= self.ledArraySize:
			forward = False
		if led <= 0:
			forward = True

		prevLed = led

		if forward == True:
			led += 1
		else:
			led -= 1

		self.changeColor(led, color)
		step += 1

		return True





