#!/usr/bin/env python

import lightserver
from lights import OpenCvDriver, LightArray

leds = lightserver.LightArrayServer(10, OpenCvDriver((20,20,20,20)))

leds.run()
