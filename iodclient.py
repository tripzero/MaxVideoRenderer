#!/usr/bin/env python

import dbus

class IodClient(dbus.Interface):
	pwm = []

	def __init__(self):
		dbus.Interface.__init__(self, dbus.SystemBus().get_object("@DBUS_SERVICE@", "/"), '@INTERFACE_PREFIX@')

		pwmPaths = self.GetPwmPaths()

		for path in pwmPaths:
			p = dbus.Interface(dbus.SystemBus().get_object('@DBUS_SERVICE@', path), "@INTERFACE_PREFIX@.Pwm")
			self.pwm.append(p)
