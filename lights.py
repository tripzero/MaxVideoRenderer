#/usr/bin/env python

import numpy as np
from gi.repository import GObject

class Id:
	id = None
	staticId = 0
	def __init__(self):
		self.id = Id.staticId
		Id.staticId += 1

class Promise:
	success = None
	args = None
	def then(self, success, *args):
		self.success = success
		if len(args) > 0:
			self.args = args

	def call(self):
		if self.success == None:
			return
		if self.args is not None:
			self.success(*self.args)
		else:
			self.success()
		return False

class Chase(Id):
	steps = 0
	step = 0
	led = 0
	color = (0,0,0)
	forward = True
	promise = None
	prevColor = (0,0,0)

	def __init__(self, color, steps):
		Id.__init__(self)
		self.color = color
		self.steps = steps
		self.promise = Promise()

class TransformToColor(Id):
	targetColor = [0,0,0]
	led = 0
	promise = None
	def __init__(self, led, targetColor):
		Id.__init__(self)
		self.led = led
		self.targetColor = targetColor
		self.promise = Promise()

	def complete(self):
		self.promise.call()

class BaseAnimation:
	animations = []
	promise = None

	def __init__(self):
		self.promise = Promise()

	def addAnimation(self, animation, *args):
		if len(args) == 0:
			args = None
		self.animations.append((animation, args))

	def _do(self, animation):
		methodCall = animation[0]
		args = animation[1]
		if animation[1] is None:
			return methodCall()
		else:
			return methodCall(*args)

class SequentialAnimation(BaseAnimation):

	def __init__(self):
		BaseAnimation.__init__(self)

	def start(self):
		if len(self.animations) == 0:
			self.promise.call()
		animation = self.animations.pop(0)
		self._do(animation)
		return self.promise

class ConcurrentAnimation(BaseAnimation):

	def __init__(self):
		BaseAnimation.__init__(self)

	def start(self):
		for animation in self.animations:
			self._do(animation).then(self._animationComplete, animation)
		return self.promise

	def _animationComplete(self, animation):
		self.animations.remove(animation)
		if len(self.animations) == 0:
			self.promise.call()

class LightArray:
	ledArraySize = 0
	ledsData = None
	needsUpdate = False
	fps = 30
	driver = None

	def __init__(self, ledArraySize, driver):
		self.ledArraySize = ledArraySize
		self.ledsData = np.zeros((ledArraySize+1, 3), np.uint8)
		self.driver = driver

	def clear(self):
		self.ledsData[:] = (0,0,0)
		self.update()

	def update(self):
		if self.needsUpdate == False:
			GObject.timeout_add(1000/self.fps, self._doUpdate)
		self.needsUpdate = True

	def _doUpdate(self):
		if self.needsUpdate == True:
			self.driver.update(self.ledsData)
			self.needsUpdate = False
		return False

	def changeColor(self, ledNumber, color):
		self.ledsData[ledNumber] = color
		self.update()

	def chase(self, color, time, delay):
		steps = time / delay
		c = Chase(color, steps)
		GObject.timeout_add(delay, self._doChase, c)
		return c.promise

	def _doChase(self, c):
		if c.step >= c.steps:
			c.promise.call()
			return False
		if c.led >= self.ledArraySize:
			c.forward = False
		if c.led <= 0:
			c.forward = True
		#restore previous led color
		self.changeColor(c.led, c.prevColor)

		if c.forward == True:
			c.led += 1
		else:
			c.led -= 1

		c.prevColor = self.ledsData[c.led]
		print c.prevColor
		self.changeColor(c.led, c.color)
		c.step += 1

		return True

	def transformColorTo(self, led, color, time):
		prevColor = self.ledsData[led]
		steps = [color[0] - prevColor[0], color[1] - prevColor[1], color[2] - prevColor[2]]
		stepsAbs = [abs(steps[0]), abs(steps[1]), abs(steps[2])]
		maxSteps = max(stepsAbs)
		if maxSteps == 0:
			maxSteps = 1
		delay = time / maxSteps
		t = TransformToColor(led, color)
		GObject.timeout_add(delay, self._doTransformColorTo, t)
		return t.promise

	def _doTransformColorTo(self, transform):
		stillTransforming = False
		color = self.ledsData[transform.led]
		for i in xrange(3):
			if color[i] < transform.targetColor[i]:
				color[i] += 1
				stillTransforming = True
			elif color[i] > transform.targetColor[i]:
				color[i] -= 1
				stillTransforming = True
		self.ledsData[transform.led] = color
		self.update()
		if stillTransforming == False:
			transform.complete()
		return stillTransforming

class Ws2801Driver:
	spiDev = None

	def __init__(self):
		import mraa
		self.spiDev = mraa.Spi(0)

	def update(self, ledsData):
		self.spiDev.write(bytearray(np.getbuffer(ledsData)))

class Apa102Driver:
	spiDev = None

	def __init__(self, freqs=1000000):
		import mraa
		self.spiDev = mraa.Spi(0)
		self.spiDev.frequency(freqs)

	def update(self, ledsData):
		data = bytearray()
		data += chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00)
		for rgb in ledsData:
			data += chr(0xff)
			# apa102 is GBR because THINGS
			data += chr(rgb[1]) + chr(rgb[2]) + chr(rgb[0])

		#endframe
		data += chr(0xff) + chr(0xff) + chr(0xff) + chr(0xff)

		self.spiDev.write(data)

class OpenCvDriver:
	image = None
	size = 50
	dimensions = None

	def __init__(self, dimensions):
		self.dimensions = dimensions

	def update(self, ledsData):
		import cv2

		bottom, right, top, left = self.dimensions
		height = max(right, left, 1)
		width = max(bottom, top, 1)
		if width == 1 and right and left:
			width = 2

		if height == 1 and bottom and top:
			height = 2

		width = width * self.size
		height = height * self.size

		if self.image == None:
			self.image = np.zeros((height, width, 3), np.uint8)

		yStep = height / 8
		xStep = width / 8

		if right != 0:
			yStep = height / (right)
		if bottom != 0:
			xStep = width / (bottom)

		#bottom
		y = height
		x = 0

		if bottom:
			pos = 0
			posEnd = bottom
			for color in ledsData[pos : posEnd]:
				self.image[height - self.size : height, x : x + xStep] = color
				x += xStep

		#right
		if right:
			pos = bottom
			posEnd = pos + right
			for color in ledsData[pos : posEnd]:
				self.image[y - yStep : y, width - self.size : width] = color
				y -= yStep

		#reset steps for top and left
		yStep = height / 8
		xStep = width / 8

		if left != 0:
			yStep = height / (left)
		if top != 0:
			xStep = width / (top)

		x = width

		#top
		if top:
			pos = bottom + right
			posEnd = pos + top
			for color in ledsData[pos : posEnd]:
				self.image[0 : self.size, x - xStep : x] = color
				x -= xStep

		y = 0

		#left
		if left:
			pos = bottom + right + top
			posEnd = pos + left
			for color in ledsData[pos : posEnd]:
				self.image[y : y + yStep, 0 : self.size] = color
				y += yStep

		cv2.imshow("output", self.image)

drivers = ["Ws2801", "Apa102", "OpenCV"]
