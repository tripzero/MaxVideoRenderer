#/usr/bin/env python

import iodclient
import numpy as np
import dbus
from gi.repository import GLib

class Ws2801:
	ledsData = None
	spiDev = None

	def __init__(self, ledArraySize):
		self.ledsData = np.zeros((ledArraySize+1, 3), np.uint8)
		client = iodclient.IodClient()
		self.spiDev = client.spi[0]
		self.clear()

	def clear(self):
		self.ledsData[:] = (0,0,0)
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def updateImg(self):
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def fadeTo(self, img, fade, time):
		# fade the array 'array', from current level to 'fade' in 'time' ms
		rate = 0.5 / time
		step = 0
		GLib.timeout_add(1, self.fadeToStep, img, rate, step, time)

	def fadeToStep(self, img, rate, step, time):
		img -= img * (1 + rate)
		self.updateImg()

		step += 1
		if step >= time:
			return False
		return True



