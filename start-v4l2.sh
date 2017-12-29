#!/bin/bash

pactl load-module module-loopback source=2 sink=0

python3 v4l2player.py

