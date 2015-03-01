#!/usr/bin/env python

import mraa
import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import GObject, GLib

class MraaService(dbus.service.Object):
	
	pwm = []

	def __init__(self):
		dbus.service.Object.__init__(self, dbus.SystemBus(), "/")
		pwm0 = mraa.Pwm(22)
		pwm0.enable(True)
		self.pwm.append(pwm0)
		pwm1 = mraa.Pwm(24)
		pwm1.enable(True)
		self.pwm.append(pwm1)
		
	
	@dbus.service.method(dbus_interface='io.tripzero.maxio', in_signature='qd', out_signature='b')
	def SetPwm(self, pwm, value):
		if len(self.pwm) <= pwm:
			return False
		if self.pwm[pwm].write(value) == 0:
			return True
		return False

	@dbus.service.method(dbus_interface='io.tripzero.maxio', in_signature='q', out_signature='d')
	def GetPwm(self, pwm):
		if len(self.pwm) <= pwm:
                        raise org.freedesktop.DBus.Error.InvalidArguments()
		return self.pwm[pwm].read()

if __name__ == '__main__':
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	system_bus = dbus.SystemBus()
	name = dbus.service.BusName('io.tripzero.maxio', system_bus)
	service = MraaService()

	GObject.MainLoop().run();
