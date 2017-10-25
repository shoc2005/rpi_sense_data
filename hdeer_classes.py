# -*- coding: utf-8 -*-
"""
HungryDeer

"""

import threading
import subprocess
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
import serial as ps
import socket as sc
import os
import shutil
import termios

class Sense_board(SenseHat):
    # inherition of SenseHat for measuring concurent reading

    def __init__(self):
        # class constructor
        super(Sense_board, self).__init__()
#        SenseHat.__init__(self)
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

class MyThread(object):
    
    def __init__(self):
        super(MyThread, self).__init__()
        self.stop_ = False
        self.pause_ = False
#        logging.debug("MyThread")
    
    def m_stop(self):
        self.stop_ = True
    
    def m_stopped(self):
        
        if self.stop_:
            logging.debug("Stopped")
        return self.stop_
    
    def m_pause(self):
        self.pause_ = True
    
    def m_paused(self):
        return self.pause_
    
    def m_reset_pause(self):
        self.pause_ = False
    

class Sensehat_sensor(MyThread, threading.Thread):
    # class for SenseHat data reading using Threading

    def __init__(self, sensor_type, sense, storage_thread, raw=True, exit_counter=500, frequency='max'):
        # sensor_type: 'acc', 'bar', 'temp_hum', 'temp_pres', 'humi', 'pres', 'gyro'
        # using raw data or estimated in degrees, radians, etc.
        # frequency: 'max' then wait time = 0.001 seconds
        # frequency: 0.0 then wait time = 1.0 seconds
        # frequency: -X then wait time = X seconds
        # frequency: X then wait time = 1/X seconds
        super(Sensehat_sensor, self).__init__()
#        threading.Thread.__init__(self)
#        MyThread.__init__(self)
#        logging.debug("INIT" + str(self.stop_))
        
        self.name = None
        self.sense = sense
        self.lock = threading.Lock()
        self.exit_counter = exit_counter
        self.storage = storage_thread
        self.paused = False
        
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
            if self.m_stopped():
                break
            
            if self.m_paused():
                time.sleep(0.5)
                continue

            
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
#        threading.Thread.__init__(self)
        super(FileSaver, self).__init__()
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

class Shell_executer(object):
    # class fro shell commands execution
    
    def __init__(self):
        # class's constructor
        super(Shell_executer, self).__init__()
        pass
    
    def run(self, cmd):
        # run command and wait exit status
        args_list = cmd.split(' ')
        p = subprocess.Popen(args_list, stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out, err
    
    def get_memory_available(self, mount_point='/'):
        # returns mount point's available bytes % of usage
        
        out, err = self.run('df -a')
        
        if len(err) > 0:
            return None
        
        out_lines = out.split('\n')
        
        for line in out_lines[1:-1]:
            data = line.split(' ')
            fields = []
            for field in data:
                if field == '':
                    continue
                fields.append(field)
            if fields[5] == mount_point and fields[4][:-1] != '':
                return int(fields[3]), fields[4][:-1]
            
        return None
    
    def get_system_time_epoch(self):
        # returns current UTC time in seconds since 1970-01-01 00:00:00 UTC
        out, err = self.run('date +%s')
        
        if len(err) > 0:
            return None
        
        return long(out)
    
    def set_system_time(self, time_epoch):
        # set current time globally in the system
        curr_path = os.path.dirname(os.path.realpath(__file__))
        out, err = self.run('sudo {:s} {:d}'.format(join(curr_path, 'run_in_shell.sh'), time_epoch))
        logging.debug("Run set system time in bash script, the output:"+ out)
        if len(err) > 0:
            return False
        
        return True
    
    def shutdown(self):
        # shutdown RPI
        
        curr_path = os.path.dirname(os.path.realpath(__file__))
        out, err = self.run('sudo {:s} {:s}'.format(join(curr_path, 'run_in_shell.sh'), 'down'))
                
        logging.debug("Run shutdown in bash script, the output:"+ out)        
        if len(err) > 0:
            return False
        
        return True
    
    def disable_dtr(self, port):
        # disable DTR for USB device

        curr_path = os.path.dirname(os.path.realpath(__file__))
        out, err = self.run('sudo {:s} {:s} {:s}'.format(join(curr_path, 'run_in_shell.sh'), 'dtr', port))
                
        logging.debug("Run shutdown in bash script, the output:"+ out)        
        if len(err) > 0:
            return False
        
        return True
        
        
    
                
class Comminicator(MyThread, threading.Thread):
    # class for communication with Ardu and Host computer
    
    rpi_ip = ''
    port = 5500
    buffer_size = 1024
    socket = None
    serial = None
    
    
    
    def __init__(self, storage, usb_port='/dev/ardu', baudr=9600, usb_timeout=1.0, sense_threads = None):
        # class's constructor

#        threading.Thread.__init__(self)
        super(Comminicator, self).__init__()
        self.name = 'Communicator'
        self.shell = Shell_executer()
        # init TCP/IP local server
        
        self.socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
        self.socket.bind((self.rpi_ip, self.port))
        self.socket.settimeout(0.1)
        self.conn = None
        
        # init USB connection with the Arduino
        
#        self.shell.disable_dtr(usb_port)
        self.serial = ps.Serial()
        self.serial.port = usb_port
        self.serial.baudrate = baudr
        self.serial.timeout = usb_timeout
        
        self.serial.open()
        self.serial.reset_input_buffer()
#        print 'dtr =', self.serial.dtr
        
        self.ardu_maint_mode = True
        self.rpi_maint_mode = True
        
        self.time_synchronized = False
        
        self.sense_threads = sense_threads
        
        self.storage = storage

    
    def usb_port_listener(self):
        # listen usb port for messages from the Ardu
        pass
    
    def tcp_ip_listener(self):
        # listen TCP connection messages from the host computer
        pass
    
    def set_current_time(self, time):
        # set current time (time epoch) for RPi from Ardu or Host
        
        res = self.shell.set_system_time(time)
        if res:
            self.time_synchronized = True
        return res
    
    def turnoff_rpi_power(self, after_seconds=60):
        # send message to the ardu for waiting N seconds and then powering off the RPI
        
        return self.send_message('turn_off_rpi:{:d}'.format(after_seconds))
    
    def get_current_time(self, epoch=True):
        # get current time from RPI
        
        if self.time_synchronized:
            if epoch:
                time_epoch = self.shell.get_system_time_epoch()
                res = self.send_message('time_synch:{:d}'.format(time_epoch))
                return res
            else:
                return False
    
    def send_sleep_time(self):
        # from calendar get current/next sleeping time for the Ardu
       
        
        
        pass
    
    def send_wakeup_time(self):
        # from calendar get current/next wakeup time for the Ardu
        pass
    
    def set_ardu_mode(self, mode = 'maint'):
        # set Ardu working mode: 'maint' - maintenance True or False
        
        if mode == 'maint':
            msg = 'enable_maint'
        else:
            msg = 'disable_maint'
        #logging.debug("Send msg to ardu: " + msg)
        res = self.send_message(msg)
        
        # return True if the message was sent, overwise False
        return res
    
    def shutdown_rpi(self, force=False):
        # stops all threads and shutdown Rpi
        
        if not force:                
            self.send_wakeup_time()
            self.set_ardu_mode(mode='run')
            self.turnoff_rpi_power()

        # stop all senses threads
        for sense_thread in self.sense_threads:
            sense_thread.m_stop()
            while not sense_thread.m_stopped():
                time.sleep(0.05)
        
        self.shell.shutdown()
        
        
        
    
    def check_ardu_status(self):
        # check current status of the Ardu
        pass
    
    def check_space_avalable(self, led_on=True):
        # check space avalabale on Rpi
        bytes_, _ = self.shell.get_memory_available()
        self.send_message(str(bytes_), usb_type=False, ack_need=False)
    
    def send_message(self, message, usb_type=True, ack_need=True):
        # send message to the Ardu
        
        if usb_type:
            if self.serial is None:
                logging.debug("Error: No USB connection with Ardu!")
                return False
            bytes_ = self.serial.write(message + '\n')
            logging.debug("Send msg to USB: "+ message)
        else:
            if self.conn is None:
                logging.debug("Error: No TCP connection with Host!")
                return False
            bytes_ = self.conn.send(message + '\n')            
            logging.debug("Sent msg to TCP/IP client: "+ message)
            
        if ack_need:
            
            # init try counter
            n = 1
            
            # try to send message            
            while n <= 3: # try 3 times
            
                # USB or TCP processing
                if usb_type:
                    answ = self.read_usb_data()
                    logging.debug("Got msg from USB: "+ answ)
                else:
                    answ = self.read_tcp_data()
                    logging.debug("Got msg from TCP/IP client: "+ answ)
                    
                if answ == 'ack':
                    return True
                
                # sleep
                time.sleep(0.5)
                
                n += 1
            
            return False # if no 'ack' recieved during 3 trials
        else: # counts bytes sent
            if bytes_ == len(message) + 1:
                return True
            else:
                return False

    
    def reset_arduino(self):
        # reset arduino
        pass
    
    def clear_rpi(self):
        # clear rpi camera's frames and log files
        
        if self.rpi_maint_mode:
            return self.storage.delete_all_data()
        else:
            return False
    
    def set_maint_mode(self, maint=True):
        # enabling/disabling maint mode for the rpi and Ardu
        
        if maint:
            # set Ardu
            res = self.set_ardu_mode('maint')
            if res:
                self.ardu_maint_mode = True
                self.time_synchronized = False
            
                # pause sensing threads on the rpi
                for sense_thread in self.sense_threads:
                    sense_thread.m_pause()
                    while not sense_thread.m_paused():
                        time.sleep(0.05)
                        
                return True
            return False
                    
        else:
            # synh time from the host
            if self.rpi_maint_mode and self.time_synchronized:
            
                # disable Ardu maint mode
                res = self.set_ardu_mode('run')
                if res:
                    self.ardu_maint_mode = False
                
                    # start sensing threads on the rpi
                    for sense_thread in self.sense_threads:
                        sense_thread.m_reset_pause()
                    return True
                return False
            
        
    def read_tcp_data(self):
        # reads data from the TCP port
        
        try:        
            data = self.conn.recv(1024)
            if not data:
                return None
        except sc.timeout as e_time_out:
            return None
        
        # ignore \n or \r symbols
        line = ''
        for byte in data:
            if not(ord(byte) == 13 or ord(byte) == 10):
                line += byte
            else:
                return line
        
        return line
        
    
    def listen_tcp_client(self):
        # listen for client on port
        
        if self.conn is None:
            try:
                self.socket.listen(1)
                self.conn, addr = self.socket.accept()
                logging.debug("Connected with TCP client from {:s} adress.".format(addr))
            except sc.timeout as e:
                return False
        else:
            return True
    
    def read_usb_data(self):
        # reads data from the usb port
        
        usb_data = ''

        while self.serial.inWaiting() > 0:
            byte_ = self.serial.read(1)
#            if byte_ == '\n':
#                break
#            else:
            usb_data += byte_
        
        
        return usb_data[:-1]
    
    def get_messages(self):
        # get messages from the USB or TCP port and switch data flow
        
        while True:
            # read USB data
            if self.m_stopped():
                break

            usb_line = self.read_usb_data()
            time.sleep(0.05)
            if len(usb_line) > 0:
                
                logging.debug("Got msg from USB: " + usb_line)
                # send RPI time to Ardu
                if usb_line == 'curr_time' and len(usb_line) < 11:
                    self.send_message('ack', ack_need=False)
                    self.get_current_time()
                    
                if usb_line == 'trigger_time':
                    self.send_message('ack', ack_need=False)
                    self.send_sleep_time()
                    time.sleep(0.1)
                    self.send_wakeup_time()
                    time.sleep(0.1)
                    
                if usb_line == 'shutdown':
                    self.send_message('ack', ack_need=False)
                    self.shutdown_rpi()
                
                if usb_line.find('curr_time') == 0 and len(usb_line) > 11:
                    self.send_message('ack', ack_need=False)
                    self.set_current_time(long(usb_line[10:]))
            
            # read TCP data
            if self.listen_tcp_client():
                tcp_data = self.read_tcp_data()
                
                if tcp_data is not None:
                    # close connection by the client request
                
                    logging.debug("Got msg from TCP/IP client: " + tcp_data)
                    if tcp_data == 'logout':
                        self.conn.close()
                    
                    # synch time from the host computer
                    if tcp_data.find("time_synch") >=0:
                        time_epoch = long(tcp_data[tcp_data.find("time_synch") + 12:])
                        time_set_res = self.set_current_time(time_epoch)

                        if time_set_res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                    
                    # delete all frames and log files
                    if tcp_data == 'clean_rpi':
                        self.clear_rpi()
                        self.send_message('ack', usb_type=False, ack_need=False)
                        
                    # get available space on rpi SD
                    if tcp_data == 'memory':
                        self.check_space_avalable()
                    
                    # shutdown rpi 
                    if tcp_data == 'shutdown':
                        self.send_message('ack', usb_type=False, ack_need=False)
                        self.shutdown_rpi(force=True)
                        
                    # enable maintenance mode for the rpi
                    if tcp_data == 'enable_maint':
                        res = self.set_maint_mode(True)
                        if res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                        
                    # disable maintenance mode for the rpi
                    if tcp_data == 'disable_maint':
                        res = self.set_maint_mode(False)
                        if res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                        

                    # disable maintenance mode for the rpi and shutdown rpi
                    if tcp_data == 'disable_maint&shutdown':
                        res = self.set_maint_mode(False)
                        if res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                            self.shutdown_rpi()
                            
                    if tcp_data == 'curr_time':
                        self.send_message('ack')
                        self.get_current_time()
                        
                    if tcp_data == 'astatus':
                        self.send_message('status', usb_type=True, ack_need=False)
                    
                    
                
                    
        
    
    def push_rpi_data(self):
        # push all rpi data to the host computer using SCP or TCP client-server arch
        
        
        # send message
        # ...
                
        self.socket.close()
        pass
        
    def run(self):
        # run thread
        logging.debug("Starting")
        while True:
#            if self.m_stopped():
#                break
            self.get_messages()
            
        self.serial.close()
        if self.conn is not None:
            self.conn.close()
        logging.debug("Exiting")
        
    
    def clear_rpi_data(self):
        # delete all RPI gathered data form SD disk
        pass
    
    
        
    

class MyBuffer(object):
    # class for parallel writing in buffer from threads
    def __init__(self, root_path):
        # class's constructor
    
        super(MyBuffer, self).__init__()
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
        
class Camera_capture(MyThread, threading.Thread):
    # class for camera capturing into jpg files
    def __init__(self, name, storage_thread, path_to_save='/tmp', counter=0, 
                 framerate=12, resolution=(640, 420), sleep_time=15.0):
        super(Camera_capture, self).__init__()
#        threading.Thread.__init__(self)
        self.name = name
        self.path_to_save = path_to_save
        self.framerate = framerate
        self.resolution = resolution
        
        self.counter = counter
        self.sleep_time = sleep_time
        self.storage = storage_thread
        logging.debug("Camera thread initialized")
        self.paused = False
        

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
            if self.m_stopped():
                break
            if self.m_paused():
                time.sleep(0.5)
                continue
            
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
        

class Data_storage(object):
    # class for data gathering from different sensors and saving in files
    
    def __init__(self, path_root):
        super(Data_storage, self).__init__()
        self.buffer = MyBuffer(path_root)
        self.dump_path = self.buffer.get_current_dump_dir()
    
    def push_data(self, data):
        # push data dictionary in the buffer
        self.buffer.push_value(data)
        
    def delete_all_data(self, data):
        # delete all files in the Rpi data storage
        
        # delete all items from a root path
        all_items = [item for item in listdir(self.buffer.root_path)]
        try:
            for item_ in all_items:
                # delete item
                if isdir(item_):
                    shutil.rmtree(item_)
                else:
                    os.remove(item_)
        except:
            logging.debug("Error in log files deletion.")
            return False
        
        return True
        
class Calendar(object):
    # class for sleep and wakeup time management
    
    def __init__(self):
        super(Calendar, self).__init__()
        pass
    
    def get_sleep_time(self):
        pass
    
    def get_wakeup_time(self):
        pass
    
    