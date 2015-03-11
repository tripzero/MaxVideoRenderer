#!/usr/bin/env python

from gi.repository import GObject

import sys
import argparse

import videoplayer
import cv2
import numpy as np

from PyQt5.QtWidgets import QApplication

def colorChanged(r, g, b, id):
	#img = np.zeros((300, 300, 3), np.uint8)
	#print "id", id, "color: ", int(r), int(g), int(b)
	#cv2.rectangle(img, (0,0), (300,300), (r, g, b), -1)
	#cv2.imshow(str(id), img)
	pass

if __name__ == '__main__':
	parser = argparse.ArgumentParser(prog="maxrenderer", description='minnowboard max dlna renderer with opencv', add_help=False)
	parser.add_argument('name', help='name of renderer on the network')
	parser.add_argument('interface', help='network interface to use (ie eth0)')

	args = parser.parse_args()

	app = QApplication(sys.argv)

	player = videoplayer.Player(args.name, args.interface)
	player.colorChanged.connect(colorChanged)
	player.setMedia('file:///home/tripzero/Videos/Visual_Dreams_720.mp4')
	player.play()

	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	app.exec_()

