#!/usr/bin/env python

import json
import lights as l

with open('config.json') as config_file:
        config  = json.load(config_file)

bottom = config['bottom']['ledCount']
left = config['left']['ledCount']
right = config['right']['ledCount']
top = config['top']['ledCount']

totalLeds = bottom + left + right + top
driver = config['driver']

if driver == 'Ws2801':
	driver = l.Ws2801Driver()
elif driver == 'Apa102':
	driver = l.Apa102Driver()


leds = l.LightArray(totalLeds, driver)

leds.clear()
leds._doUpdate()






