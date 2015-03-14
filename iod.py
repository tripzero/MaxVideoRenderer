#!/usr/bin/env python

import mraa
import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import GObject

class MaxPinLayout:
	pwm = [22, 24]
	gpio = [10, 12, 14, 16, 18, 20, 21]
	i2c = 2
	spi = 1

class EdisonPinLayout:
	pwm = [20, 14, 0, 21]
	gpio = []
	i2c = 2


class Pwm(dbus.service.Object):
	pwm = None
	path = None

	def __init__(self, index, pinLayout):
		self.path = "/pwm/"+str(index)
		dbus.service.Object.__init__(self, dbus.SystemBus(), self.path)
		self.pwm = mraa.Pwm(pinLayout.pwm[index])

	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@.Pwm', in_signature='b')
	def enable(self, value):
		self.pwm.enable(value)

	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@.Pwm', in_signature='d', out_signature='b')
	def write(self, value):
		if not self.pwm:
			return False
		if self.pwm.write(value) == 0:
			return True
		return False

	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@.Pwm', out_signature='d')
	def read(self):
		if not self.pwm:
			raise org.freedesktop.DBus.Error.InvalidArguments()
		return self.pwm.read()

class Spi(dbus.service.Object):
	spi = None
	path = None

	def __init__(self, busIndex):
		self.path = "/spi/" + str(busIndex)
		dbus.service.Object.__init__(self, dbus.SystemBus(), self.path)
		self.spi = mraa.Spi(busIndex)

	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@.Spi', in_signature='ay', out_signature='ay')
	def write(self, value):
		if not self.spi:
			return ''
		return self.spi.write(bytearray(value))



class MraaService(dbus.service.Object):

	pwm = []
	spi = []
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
			self.pwm.append(p)
			i += 1

		for bus in xrange(self.pinLayout.spi):
			s = Spi(bus)
			self.spi.append(s)


	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@', out_signature='ao')
	def GetPwmPaths(self):
		paths = []
		for p in self.pwm:
			paths.append(dbus.ObjectPath(p.path))
		return paths

	@dbus.service.method(dbus_interface='@INTERFACE_PREFIX@', out_signature='ao')
	def GetSpiPaths(self):
		paths = []
		for s in self.spi:
			paths.append(dbus.ObjectPath(s.path))
		return paths


if __name__ == '__main__':
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	system_bus = dbus.SystemBus()
	name = dbus.service.BusName('@DBUS_SERVICE@', system_bus)
	service = MraaService()

	GObject.MainLoop().run();
