#!/bin/bash

cd /home/root/src/MaxVideoRenderer

export XDG_RUNTIME_DIR=/run/user/0

pulseaudio --start

pactl load-module module-loopback source=2 sink=0

python3 v4l2player.py --test