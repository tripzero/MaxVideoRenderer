#/usr/bin/env python

import iodclient
import numpy as np

class Ws2801:
	ledsData = None
	spiDev = None

	def __init__(self, numLeds):
		self.ledsData = np.zeros((numLeds,3), np.uint8)
		client = iodclient.IodClient()
		spiDev = client.spi[0]
		spiDev.write(self.ledsData.toBytes())

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		spiDev.write(self.ledsData.toBytes())

