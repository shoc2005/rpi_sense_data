#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
HungryDeer

"""

import hdeer_classes as hdc
import logging
import threading

# set debug output format
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
# Create new threads
sense = hdc.Sense_board()
storage_thread = hdc.Data_storage('/home/pi/sources/data')



thread1 = hdc.Sensehat_sensor(sensor_type='acc', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency='max')
#thread1.setDaemon(True)

thread2 = hdc.Sensehat_sensor(sensor_type='gyro', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency='max')
#thread2.setDaemon(True)

thread3 = hdc.Sensehat_sensor(sensor_type='humi', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread3.setDaemon(True)

thread4 = hdc.Sensehat_sensor(sensor_type='pres', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread4.setDaemon(True)

thread5 = hdc.Sensehat_sensor(sensor_type='temp', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread5.setDaemon(True)

thread6 = hdc.Camera_capture(name='rpiCamera', storage_thread = storage_thread, path_to_save=hdc.join(storage_thread.dump_path, 'images'),
                         sleep_time=12.0)
#thread6.setDaemon(True)

thread7 = hdc.Comminicator(storage_thread, sense_threads = [thread1, thread2, thread3, thread4, thread5, thread6])
thread7.setDaemon(True)

# Start new Threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
thread6.start()
thread7.start()

main_thread = threading.currentThread()
for t in threading.enumerate():
    if t is main_thread or t.getName() == 'rpiCamera':
        continue
    
    logging.debug('joining %s', t.getName())
    t.join()

#thread1.join(14.5)
#thread2.join()
