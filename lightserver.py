from twisted.internet import gireactor
gireactor.install()

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS, WebSocketClientProtocol, WebSocketClientFactory, connectWS

from twisted.internet import reactor
from twisted.python import log

from lights import LightArray
from threading import Thread
import sys
import numpy as np
import struct

#log.startLogging(sys.stdout)

class LightArrayServer(LightArray):
	def __init__(self, numLeds, driver):
		LightArray.__init__(self, numLeds, driver)

		ServerProtocol.lightServer = self

		factory = WebSocketServerFactory("ws://localhost:5000")
		factory.protocol = ServerProtocol

		listenWS(factory)

	def run(self):
		reactor.run()

class ServerProtocol(WebSocketServerProtocol):
	lightServer = None
	debug=True
	debugCodePaths=True

	def onOpen(self):
		print("can has connection!")

	def onMessage(self, payload, isBinary):
		print("got a message: ", len(payload))
		if not isBinary:
			return

		payload = np.frombuffer(payload, np.uint8)

		cmd = payload[0]

		print("cmd=", cmd)

		if cmd == 0x01:
			self.setLights(payload)
		elif cmd == 0x02:
			self.setNumLights(payload)
		elif cmd == 0x03:
			self.clear()

	def setLights(self, payload):
		print('setting lights')
		lsb = payload[1]
		numLights = payload[2] << 8 | lsb
		payload = payload[3:]
		n = 0
		while n < len(payload):
			lightData = payload[n:n+5]
			lsb = lightData[0]
			id = lightData[1] << 8 | lsb
			r = lightData[2]
			g = lightData[3]
			b = lightData[4]

			ServerProtocol.lightServer.changeColor(id, (r,g,b))
			n+=5

	def setNumLights(self, payload):
		print('setting number of lights')
		lsb = payload[1]
		numLights = payload[2] << 8 | lsb

		ServerProtocol.lightServer.setLedArraySize(numLights)

	def clear(self):
		print('clearing')
		ServerProtocol.lightServer.clear()

	def connectionLost(self, reason):
		WebSocketServerProtocol.connectionLost(self, reason)

class WSClientDriver(WebSocketClientFactory):
	server = None
	ledsDataCopy = None

	def __init__(self, address, port):
		WebSocketClientFactory.__init__(self, "ws://{0}:{1}".format(address, port), debug=True, origin='null')

		self.protocol = WSClientProtocol

		connectWS(self)

	def register(self, server):
		self.server = server

	def update(self, ledsData):
		if not self.server:
			return

		if self.ledsDataCopy is None:
			self.ledsDataCopy = np.array(ledsData, copy=True)
			self.setNumLeds(len(self.ledsDataCopy))

		diff = np.bitwise_xor(ledsData, self.ledsDataCopy)

		ledsToChange = bytearray()

		for i in xrange(len(diff)):
			if not np.all(np.equal(diff[i], [0,0,0])):
				ledsToChange.extend(struct.pack('<H', i))
				ledsToChange.extend(ledsData[i])

		header = bytearray()
		header.append(0x01)
		header.extend(struct.pack('<H', len(ledsToChange)))
		ledsToChange = header + ledsToChange

		self.ledsDataCopy = np.array(ledsData, copy=True)

		self.send(ledsToChange)

	def send(self, msg):
		msg = bytes(msg)
		if self.server:
			print("sending:", msg)
			self.server.sendMessage(msg, True)

	def setNumLeds(self, numLeds):
		buff = bytearray()
		buff.append(0x02)
		buff.extend(struct.pack('<H', numLeds))
		self.send(buff)

	def unregister(self):
		self.server = None

	def run(self):
		reactor.run()

class WSClientProtocol(WebSocketClientProtocol):
	debug=False
	debugCodePaths=False

	def onConnect(self, response):
			print("Server connected: {0}".format(response.peer))

	def onOpen(self):
		print("WebSocket connection open.")
		self.factory.register(self)

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			print("Text message received: {0}".format(payload.decode('utf8')))

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))
		self.factory.unregister()
