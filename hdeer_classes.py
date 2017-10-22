# -*- coding: utf-8 -*-
"""
HungryDeer

script contains classes for the Sense Hat data gathering using Threading,
communication between rpi and arduino (rpi side), events logging class, etc.

"""

import threading
import time
from sense_hat import SenseHat
import logging
import struct
from picamera import PiCamera
from os.path import join
from os import listdir
from os.path import isdir
from os import makedirs
from os.path import exists
import datetime



class sense_board(SenseHat):
    # inherition of SenseHat for measuring concurent reading

    def __init__(self):
        # class constructor
        SenseHat.__init__(self)
        self.lock = threading.Lock()
    
    def get_measurment(self, m_type):
        # get sensor's values
        self.lock.acquire()
        try:
            t1 = time.time()
            sensor_values = m_type()
        finally:
            self.lock.release()                
        return t1, sensor_values

class sensehat_sensor(threading.Thread):
    # class for SenseHat data reading using Threading

    def __init__(self, sensor_type, sense, storage_thread, raw=True, exit_counter=500, frequency='max'):
        # sensor_type: 'acc', 'bar', 'temp_hum', 'temp_pres', 'humi', 'pres', 'gyro'
        # using raw data or estimated in degrees, radians, etc.
        # frequency: 'max' then wait time = 0.001 seconds
        # frequency: 0.0 then wait time = 1.0 seconds
        # frequency: -X then wait time = X seconds
        # frequency: X then wait time = 1/X seconds
    
        threading.Thread.__init__(self)
    
        self.name = None
        self.sense = sense
        self.lock = threading.Lock()
        self.exit_counter = exit_counter
        self.storage = storage_thread
        
        if frequency == 'max':
            self.read_wait_time = 1.0/1000
        elif frequency < 0:
            self.read_wait_time = abs(frequency)
        elif frequency == 0.0:
            self.read_wait_time = 1.0
        else:
            self.read_wait_time = 1.0 / frequency
    
        assert sensor_type in ['acc', 'temp_hum', 'temp_pres', 'humi', 'pres', 'gyro', 'temp']
        if sensor_type == 'acc':
            self.name = 'Accelerometer'
            
            if raw:
                self.measure = self.sense.get_accelerometer_raw
                self.type_name = 'ACR'
                logging.debug("Using Accelerometer, measurements in Gs")
            else:
                self.measure = self.sense.get_accelerometer
                self.type_name = 'ACN'
                logging.debug("Using Accelerometer, measurements in degrees")

            
        if sensor_type == 'gyro':
            self.name = 'Gyroscope'
            if raw:
                self.measure = self.sense.get_gyroscope_raw
                self.type_name = 'GYR'
                logging.debug("Using Gyroscope, measurements in radians per second")
            else:
                self.measure = self.sense.get_gyroscope
                self.type_name = 'GYN'
                logging.debug("Using Gyroscope, measurements in degrees")

        if sensor_type == 'humi':
            self.name = 'Humidity'
            self.measure = sense.get_humidity
            self.type_name = 'HUN'
            logging.debug("Using Humidity sensor, measurements in percentage")

        if sensor_type == 'pres':
            self.name = 'Barometer'
            self.type_name = 'BAN'
            self.measure = sense.get_pressure
            logging.debug("Using Barometer sensor, measurements in Millibars")

#        if sensor_type == 'temp_hum':
            self.name = "Humidity sensor's temperature"
            self.measure = sense.get_temperature_from_humidity
            self.type_name = 'HTN'
            logging.debug("Using Humidity sensor, measurement degrees in Celsius")

        if sensor_type == 'temp_pres':
            self.name = "Barometer sensor's temperature"
            self.type_name = 'PTN'
            self.measure = sense.get_temperature_from_pressure
            logging.debug("Using Humidity sensor, measurement degrees in Celsius")           

        if sensor_type == 'temp':
            self.name = "Board sensor's temperature"
            self.type_name = 'BTN'
            self.measure = sense.get_temperature
            logging.debug("Using board sensor, measurement degrees in Celsius")

    def run(self):
        # enter point in the Thread
        logging.debug("Starting")
        self.read_value()
        logging.debug("Exiting")
        logging.debug("is deamon {:b}".format(self.isDaemon()))
    
    def read_value(self):
        # reads the sensor value from the SenseHat method
        t1 = time.time()
        counter = 0
        
        while self.exit_counter > 0:
            val_time, sensor_values = self.sense.get_measurment(self.measure)
            self.storage.push_data({'sense_hat':sensor_values, 'sense_type': self.type_name, 'time': val_time})
#            logging.debug("{:f} - {:s}".format(time.time(), str(sensor_values)))
            time.sleep(self.read_wait_time)
            counter += 1
            if time.time() - t1 >= 10.0:
                logging.debug("fps is {:.2f}".format(counter / 10.0))
                t1 = time.time()
                counter = 0
            # self.exit_counter -= 1

class FileSaver(threading.Thread):
    # file provides saving in binary file all recorded data
    
    def __init__(self, name, data, file_name):
        threading.Thread.__init__(self)
        self.name = name
        self.data = data
        
        self.file_name = file_name
    
    def run(self):
        # enter point in the Thread
        logging.debug("Starting")
        self.save_data()
        logging.debug("Exiting")
        
    def save_data(self):
        # save all data into the binary file
        
        f = open(self.file_name, 'wb')
        # write header to the file - description on data fields used
        f.write("KEYC_s:TIME_f:\n") # where first three is sense_hat type name and last is N or component name X, Y or Z
                                 # or KEYC is IMAG - means the image data        
        # process sense hat data
        for item in self.data:
            
            if item.has_key('sense_hat'):
                if type(item['sense_hat']) is dict:
                    bytes2write = struct.pack('<fffd', item['sense_hat']['x'], 
                                              item['sense_hat']['y'], 
                                            item['sense_hat']['z'], item['time'])
                    f.write(item['sense_type']+'C')
                else:
                    bytes2write = struct.pack('<fd', item['sense_hat'], item['time'])
                    f.write(item['sense_type']+'N')
                
                f.write(bytes2write)
                
            elif item.has_key('image'):
                f.write('IMAG')
                bytes2write = struct.pack('<Id', item['image'], item['time'])
                f.write(bytes2write)
            
        f.close()
        logging.debug("File written")
                


class MyBuffer:
    # class for parallel writing in buffer from threads
    def __init__(self, root_path):
        # class constructor
        self.stack = []
        self.stack_size = 25000
        self.lock = threading.Lock()
        self.file_counter = 0
        self.root_path = root_path
        self.dump_path = self.check_last_dir()
    
    def get_current_dump_dir(self):
        return self.dump_path
    
    def check_last_dir(self):
        # check the last dump directory in the root path and creates one new
        
        # get list with directories in the root
        dirnames_all = [dirname for dirname in listdir(self.root_path) if isdir(join(self.root_path, dirname))]
        
        # get last id
        dump_ids = []
        for name in dirnames_all:
            vals = name.split('_') # directory name format: 'dump id dd.mm.yyyy'
            if len(vals) == 3:
                try:
                    dump_ids.append(int(vals[1])) # add only id 
                except:
                    logging.debug("Something wrong with directory name format for dump files and images")
        
        # make new directory
        if len(dump_ids) > 0:
            max_id = max(dump_ids)
            max_id += 1
        else:
            max_id = 1
            
        date = datetime.datetime.now()
        new_dir = "dump_{:d}_{:s}".format(max_id, date.strftime('%d.%m.%Y'))
        makedirs(join(self.root_path, new_dir))
            
        return join(self.root_path, new_dir)
        
        
    
    def push_value(self, value):
        with self.lock:
            self.stack.append(value)
            if len(self.stack) >= self.stack_size:
                full_stack = self.stack
                self.stack = []
                self.save_to_file(full_stack,  
                                  join(self.dump_path, "dump_{:06d}.bin".format(self.file_counter)))
                
    
    def save_to_file(self, data, file_name):
        new_thread = FileSaver('FileSaver_' + str(self.file_counter), data, file_name)
        self.file_counter += 1
        new_thread.start()
        new_thread.join()
        
class camera_capture(threading.Thread):
    # class for camera capturing into jpg files
    def __init__(self, name, storage_thread, path_to_save='/tmp', counter=0, 
                 framerate=12, resolution=(640, 420), sleep_time=15.0):
        threading.Thread.__init__(self)
        self.name = name
        self.path_to_save = path_to_save
        self.framerate = framerate
        self.resolution = resolution
        
        self.counter = counter
        self.sleep_time = sleep_time
        self.storage = storage_thread
        logging.debug("Camera thread initialized")
        

    def run(self):
        # enter point in the Thread
        
        if not exists(self.path_to_save):
            makedirs(self.path_to_save)
    
        logging.debug("Starting")
        self.capture()
        logging.debug("Exiting")

    def capture(self):
        # capture images in sequence
        prep_time = 2.0
        
        while True:
            camera = PiCamera()
            time.sleep(prep_time)
            camera.framerate = self.framerate
            camera.resolution = self.resolution
            camera.capture(join(self.path_to_save, 'img{:05d}.jpg'.format(self.counter)), format='jpeg', quality = 70)
            logging.debug("Camera capture") 
            camera.close()
            self.storage.push_data({'image': self.counter, 'time': time.time()})
            time.sleep(abs(self.sleep_time - prep_time))
            self.counter += 1
        

class data_storage():
    # class for data gathering from different sensors and saving in files
    
    def __init__(self, path_root):
        self.buffer = MyBuffer(path_root)
        self.dump_path = self.buffer.get_current_dump_dir()
    
    def push_data(self, data):
        # push data dictionary in the buffer
        self.buffer.push_value(data)


# set debug output format
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
# Create new threads
sense = sense_board()
storage_thread = data_storage('/home/pi/sources/data')



thread1 = sensehat_sensor(sensor_type='acc', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency='max')
#thread1.setDaemon(True)

thread2 = sensehat_sensor(sensor_type='gyro', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency='max')
#thread2.setDaemon(True)

thread3 = sensehat_sensor(sensor_type='humi', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread3.setDaemon(True)

thread4 = sensehat_sensor(sensor_type='pres', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread4.setDaemon(True)

thread5 = sensehat_sensor(sensor_type='temp', sense=sense, storage_thread = storage_thread, exit_counter=2000, frequency=-60.0)
#thread5.setDaemon(True)

thread6 = camera_capture(name='rpiCamera', storage_thread = storage_thread, path_to_save=join(storage_thread.dump_path, 'images'),
                         sleep_time=12.0)
thread6.setDaemon(True)

# Start new Threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
thread6.start()

main_thread = threading.currentThread()
for t in threading.enumerate():
    if t is main_thread or t.getName() == 'rpiCamera':
        continue
    logging.debug('joining %s', t.getName())
    t.join()
#thread1.join(14.5)
#thread2.join()
