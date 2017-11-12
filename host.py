# -*- coding: utf-8 -*-
"""
Created on Thu Nov 09 16:46:40 2017

@author: sholc2005
"""


import logging
import threading
#import os
from os.path import join

# set debug output format
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s (%(threadName)-10s) %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S',
                    filename=join('/home/hrpi/data_sync', 'host.log')
                    )
import hdeer_classes as hdc
thread1 = hdc.HostPC()

logging.debug('Started')
#thread1.setDaemon(True)

thread1.start()

main_thread = threading.currentThread()
for t in threading.enumerate():
    if t is main_thread:
        continue
    
    logging.debug('joining %s', t.getName())
    t.join()
