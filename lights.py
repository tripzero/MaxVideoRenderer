#/usr/bin/env python

import iodclient
import numpy as np

class Ws2801:
	ledsData = None
	spiDev = None

	def __init__(self, ledArraySize):
		self.ledsData = np.zeros((ledArraySize, 3), np.uint8)
		client = iodclient.IodClient()
		spiDev = client.spi[0]
		spiDev.write(self.ledsData.tostring())

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		spiDev.write(self.ledsData.tostring())

