#!/usr/bin/env python

import sys
import videoplayer
import time

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

app = QApplication(sys.argv)

player = videoplayer.Player('weeee', 'eth0')

player.setMedia('file:///home/tripzero/Videos/Visual_Dreams_720.mp4')
player.play()

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

#def pause():
#	player.pause()

#timer = QTimer()
#timer.timeout.connect(pause)
#timer.start(5000)

app.exec_()
