#/usr/bin/env python

import iodclient
import numpy as np
import dbus

class Ws2801:
	ledsData = None
	spiDev = None

	def __init__(self, ledArraySize):
		self.ledsData = np.zeros((ledArraySize, 3), np.uint8)
		client = iodclient.IodClient()
		self.spiDev = client.spi[0]

	def clear(self):
		self.ledsData[:] = (0,0,0)
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		self.spiDev.write(dbus.ByteArray(self.ledsData.tostring()))

