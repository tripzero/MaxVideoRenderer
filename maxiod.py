#!/usr/bin/env python3

import mraa
import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import GObject

class i2cObject:
	scl = None
	sda = None

	def __init__(self, scl, sda):
		self.scl = scl
		self.sda = sda

class MaxPinLayout:
	pwm = [22, 24]
	gpio = [10, 12, 14, 16, 18, 20, 21]
	i2c = [i2cObject(13,15)]


class EdisonPinLayout:
	pwm = [20, 14, 0, 21]
	gpio = []
	i2c = [i2cObject(19, 7), i2cObject(6, 8)]


class Pwm(dbus.service.Object):
	pwm = None
	path = None

	def __init__(self, index, pinLayout):
		self.path = "/pwm"+index
		dbus.service.Object.__init__(self, dbus.SystemBus(), self.path)
		self.pwm = mraa.Pwm(pinLayout.pwm[index])

	@dbus.service.method(dbus_interface='io.tripzero.maxio.Pwm', in_signature='b')
	def enable(self, value):
		self.pwm.enable(value)

	@dbus.service.method(dbus_interface='io.tripzero.maxio.Pwm', in_signature='d', out_signature='b')
	def write(self, value):
		if not pwm:
			return False
		if self.pwm.write(value) == 0:
			return True
		return False

	@dbus.service.method(dbus_interface='io.tripzero.maxio.Pwm', out_signature='d')
	def read(self):
		if not pwm:
			raise org.freedesktop.DBus.Error.InvalidArguments()
		return self.pwm.read()


class MraaService(dbus.service.Object):

	pwm = []
	pinLayout = None

	def __init__(self):
		dbus.service.Object.__init__(self, dbus.SystemBus(), "/")

		platform = mraa.getPlatformName()

		if platform == 'MinnowBoard MAX':
			self.pinLayout = MaxPinLayout()
		elif platform == 'Intel Edison':
			self.pinLayout = EdisonPinLayout()

		if not self.pinLayout:
			raise Exception("platform unknown: " + platform)

		i = 0
		for pin in self.pinLayout.pwm:
			p = Pwm(i, self.pinLayout)
			pwm.append(p)
			i += 1


	@dbus.service.method(dbus_interface='io.tripzero.maxio', out_signature='ao')
	def GetPwmPaths(self):
		paths = []
		for p in pwm:
			paths.append(dbus.ObjectPath(p.path))
		return paths



if __name__ == '__main__':
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	system_bus = dbus.SystemBus()
	name = dbus.service.BusName('io.tripzero.maxio', system_bus)
	service = MraaService()

	GObject.MainLoop().run();
