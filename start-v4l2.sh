#!/bin/bash

cd /home/root/src/MaxVideoRenderer

export XDG_RUNTIME_DIR=/run/user/0

modprobe low-speed-spidev

pulseaudio --start

pactl set-card-profile  output:hdmi-stereo
pactl load-module module-loopback source=0 sink=0

python3 v4l2player.py