# -*- coding: utf-8 -*-
"""
HungryDeer

"""

import threading
import subprocess
import time
import logging
#import sys

try:
    from sense_hat import SenseHat
except:
    class SenseHat(object):
        # fake class
        def __init__(self):
            pass
        
    logging.debug("Error: SenseHat lib not found!")
    

import struct

try:
    from picamera import PiCamera
except:
    class PiCamera(object):
        # fake class
        def __init__(self):
            pass
        
    logging.debug("Error: PiCamera lib not found!")
    
from os.path import join
from os import listdir
from os.path import isdir
from os.path import isfile
from os import makedirs
from os.path import exists
import datetime
import serial as ps
import socket as sc
import os
import shutil
import random
import stat

class Sense_board(SenseHat):
    # inherition of SenseHat for measuring concurent reading

    def __init__(self):
        # class constructor
        super(Sense_board, self).__init__()
#        SenseHat.__init__(self)
        self.lock = threading.Lock()
        self.active_leds = [(3,5), (3,3), (3,1)]
    
    def get_measurment(self, m_type):
        # get sensor's values
#        logging.debug("Waiting get_measurement")
        self.lock.acquire()
        
        try:
            
            t1 = time.time()
            sensor_values = m_type()
#            logging.debug("Acquired get_measurement")
        finally:
            self.lock.release()
#            logging.debug("Released get_measurement")
        return t1, sensor_values
    
    def set_led_color(self, color=(255, 255, 255), led_id = None):
        # set color for a particular led in the active_leds list or for all leds in the list if led_id is None
        
        self.lock.acquire()
        
        if led_id is None and len(self.active_leds) > 0:
            for led in self.active_leds:
                try:
                    self.set_pixel(led[0], led[1], color)
                except:
                    logging.debug("Error: can´t set color {:s} to the led {:s}.".format(str(color), str(led)))
                    
        elif len(self.active_leds) > 0:
            
            if type(led_id) is not list:
                if led_id not in range(0, len(self.active_leds)):
                    logging.debug("Error: ledID {:d} is not correct.".format(led_id))
                    return
                leds = [self.active_leds[led_id]]
            else:
                leds = []
                for le_id in led_id:
                    if le_id not in range(0, len(self.active_leds)):
                        logging.debug("Error: ledID {:d} is not correct.".format(led_id))
                        continue
                    leds.append(self.active_leds[le_id])
                
            
            for led in leds:
                try:
                    self.set_pixel(led[0], led[1], color)
                except:
                    logging.debug("Error: can´t set color {:s} to the led {:s}.".format(str(color), str(led)))
        else:
            logging.debug("Erro: active led list is empty.")
            
        self.lock.release()
    
    def reset_leds(self):
        
        self.set_led_color(color=(0, 0, 0))
                    

class MyThread(object):
    
    def __init__(self):
        super(MyThread, self).__init__()
        self.stop_ = False
        self.pause_ = True
#        logging.debug("MyThread")
    
    def m_stop(self, name='self'):
        self.stop_ = True
        logging.debug("Stopped for {:s}".format(name))
    
    def m_stopped(self):
        
#        if self.stop_:
#            logging.debug("Stopped")
        return self.stop_
    
    def m_pause(self, name='self'):
        self.pause_ = True
        logging.debug("Paused for {:s}".format(name))
    
    def m_paused(self):
        return self.pause_
    
    def m_reset_pause(self, name='self'):
        self.pause_ = False
        logging.debug("Resumed for {:s}".format(name))
    

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
        self.t1 = time.time()
        self.counter = 0
        
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
        if self.m_paused():
            logging.debug("Starting in paused mode")
        else:
            logging.debug("Starting")
            
        self.read_value()
        logging.debug("Exiting")
        logging.debug("is deamon {:b}".format(self.isDaemon()))
    
    def read_value(self):
        # reads the sensor value from the SenseHat method
        self.t1 = time.time()
        self.counter = 0
        
        while self.exit_counter > 0:
            if self.m_stopped():
                break
            
            if self.m_paused():
                r = random.random()
                time.sleep(r)
                continue

            
            val_time, sensor_values = self.sense.get_measurment(self.measure)
            self.storage.push_data({'sense_hat':sensor_values, 'sense_type': self.type_name, 'time': val_time})
#            logging.debug("Pushed data")
#            logging.debug("{:f} - {:s}".format(time.time(), str(sensor_values)))
            time.sleep(self.read_wait_time + random.random() / 1000.0)
            self.counter += 1
            if time.time() - self.t1 >= 180.0:
                logging.debug("fps is {:.2f}".format(self.counter / 180.0))
                self.t1 = time.time()
                self.counter = 0
                
    def m_reset_pause(self, name='self'):
        # resume thread from pause

        self.t1 = time.time()
        self.counter = 0
        self.pause_ = False
        logging.debug("Resumed for {:s}".format(name))

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
        flags = os.O_WRONLY|os.O_CREAT|os.O_APPEND
        mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        f = os.open(self.file_name, flags, mode)
#        f = open(self.file_name, 'wb')
        # write header to the file - description on data fields used
        os.write(f, "KEYC_s:TIME_f:\n") # where first three is sense_hat type name and last is N or component name X, Y or Z
                                 # or KEYC is IMAG - means the image data        
        # process sense hat data
        for item in self.data:
            
            if item.has_key('sense_hat'):
                if type(item['sense_hat']) is dict:
                    bytes2write = struct.pack('<fffd', item['sense_hat']['x'], 
                                              item['sense_hat']['y'], 
                                            item['sense_hat']['z'], item['time'])
                    os.write(f, item['sense_type']+'C')
                else:
                    bytes2write = struct.pack('<fd', item['sense_hat'], item['time'])
                    os.write(f, item['sense_type']+'N')
                
                os.write(f, bytes2write)
                
            elif item.has_key('image'):
                os.write(f, 'IMAG')
                bytes2write = struct.pack('<Id', item['image'], item['time'])
                os.write(f, bytes2write)
            
        os.close(f)
        new_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        os.chmod(self.file_name, new_mode)
        
        logging.debug("File was written")

class Shell_executer(object):
    # class fro shell commands execution
    
    def __init__(self):
        # class's constructor
        super(Shell_executer, self).__init__()
        pass
    
    def run(self, cmd):
        # run command and wait exit status
#        args_list = cmd.split(' ')
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        return out, err
    
    def copy_files_via_ssh(self, host_ip, from_path, to_path, from_user = None, to_user = None):
        # copy all files from the path to the path via the scp command tool for linux
        
        if to_user is None and from_user is None:
            logging.debug("Error: using scp - from and to user parameter is None")
            return False
        
        if from_user is not None:
            cmd = 'scp -p -r {:s}@{:s}:{:s} {:s}'.format(from_user, host_ip, from_path, to_path)
        elif to_user is not None:
            cmd = 'scp -p -r {:s} {:s}@{:s}:{:s}'.format(from_path, to_user, host_ip, to_path)
        
        out, err = self.run(cmd)
        
        if len(err) > 0:
            logging.debug("Error: using scp something is wrong with command: " + cmd)
            logging.debug("Scp command error: " + err)
            return False
        
        return True
   
        
    
    def get_memory_available(self, mount_point='/'):
        # returns mount point's available bytes % of usage
        
        out, err = self.run('df -a')
        
        if len(err) > 0:
            return None, None
        
        out_lines = out.split('\n')
        
        for line in out_lines[1:-1]:
            data = line.split(' ')
            fields = []
            for field in data:
                if field == '':
                    continue
                fields.append(field)
            if fields[5] == mount_point and fields[4][:-1] != '':
                return int(fields[3]), int(fields[4][:-1])
            
        return None, None
    
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
            logging.debug("Error (run set system time): " + err)
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
    
    
    
    def __init__(self, storage, hat, usb_port='/dev/ardu', baudr=9600, 
                 usb_timeout=1.0, sense_threads = None, rpi_ip = ''):
        # class's constructor

#        threading.Thread.__init__(self)
        super(Comminicator, self).__init__()
        self.name = 'Communicator'
        self.shell = Shell_executer()
        self.hat = hat
        # init TCP/IP local server
        
        self.socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
        self.socket.bind((self.rpi_ip, self.port))
        self.time_out_tcp = 0.1
        self.socket.settimeout(self.time_out_tcp)
        
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
        
        self.calendar = Calendar()
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        calendar_file = join(curr_dir, 'calendar.txt')
        self.calendar.load_calendar_from_file(calendar_file)
        
        self.scheduled_shutdown = False
        self.user_activity = None
#        self.set_user_activity()
        self.beep_on = False
        
    
    
    def set_user_activity(self):
        # sets user's activity time
        self.user_activity = time.time()
    
    def get_user_last_activity_tinterval(self):
        # returns time inteval between the last user's activity
        
        return time.time() - self.user_activity    
        

    
    def usb_port_listener(self):
        # listen usb port for messages from the Ardu
        pass
    
    def tcp_ip_listener(self):
        # listen rpi and connect to it
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pass
    
    def set_current_time(self, time):
        # set current time (time epoch) for RPi from Ardu or Host
        
        res = self.shell.set_system_time(time)
        if res:
            self.time_synchronized = True
            
        return res
    
    def setup_triggers(self):
        
        wake_, down_, in_between = self.calendar.get_sleep_up_time(in_epoch = True)
        logging.debug("Nearest time found: UP{:s}, down{:s}".format(str(wake_), str(down_)))
        
        counter = 1
        while counter <= 5:
            res = self.send_wakeup_time(wake_)
            if res:
                break
            time.sleep(0.7)
            counter += 1
            
        counter = 1 
        while counter <= 5:
            res = self.send_sleep_time(down_)
            if res:
                break
            time.sleep(0.7)
            counter += 1
    
    def prepare_to_shutdown_rpi(self):

        wake_, down_, in_between = self.calendar.get_sleep_up_time(in_epoch = True)                   
                    
        # prevent shutdown if rpi's current time is between wakeup and shutdown times
        
        if in_between:
            self.scheduled_shutdown = False
            logging.debug("Shutdown canceled - between UP and DOWN time.")
            return
            
        self.setup_triggers()
        self.scheduled_shutdown = 'run'

        
        
    
    def turnoff_rpi_power(self, after_seconds=20):
        # send message to the ardu for waiting N seconds and then powering off the RPI
        if self.beep_on:
            tag = 'usr'
        else:
            tag = ''
        
        msg = 'turn_off_rpi{:s}:{:d}'.format(tag, after_seconds)
        
        return self.send_message(msg)
    
    def get_ardu_time(self):
        # gets current time from Ardu
    
        return self.send_message('get_ardu_time')
    
    def get_current_time(self, epoch=True):
        # get current time from RPI
        
        if self.time_synchronized:
            if epoch:
                time_epoch = self.shell.get_system_time_epoch()
                while True:
                    res = self.send_message('time_synch:{:d}'.format(time_epoch))
                    if res:
                        break
                    time.sleep(0.2)
                    
                return True
            else:
                return False
        else:
            return False
    
    def send_sleep_time(self, epoch):
        # set sleep time for the Rpi

        res = self.send_message('sleep_time:{:d}'.format(epoch))
        
        if res:
            return True
        else:
            return False
    
    def send_wakeup_time(self, epoch):
        # set wakeup time for the RPi
    
        res = self.send_message('wakeup_time:{:d}'.format(epoch))
        
        if res:
            return True
        else:
            return False
    
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
            self.turnoff_rpi_power(20)
            time.sleep(1.2)
            
        for sense_thread in self.sense_threads:
            sense_thread.m_stop(sense_thread.getName())
            while not sense_thread.m_stopped():
                time.sleep(0.05)
        self.shell.shutdown()
        
        
    
        
    
    def show_rpi_status(self, led_on_after= 1.0, led_off_after=5.0):
        # check space avalabale on Rpi
        
        bytes_, percen = self.shell.get_memory_available()


        if not self.time_synchronized and self.rpi_maint_mode:
            t = threading.Timer(led_on_after, self.hat.set_led_color, [(255, 0, 0), 0]) # white
            t.start()
            
        elif self.rpi_maint_mode:
            t = threading.Timer(led_on_after, self.hat.set_led_color, [(255, 255, 0), 0]) # yellow
            t.start()
        else:
            t = threading.Timer(led_on_after, self.hat.set_led_color, [(0, 255, 0), 0]) # green
            t.start()


        
        if bytes_ is not None:
            
            # Total 8Gb of 16Gb is available 50% in clean rpi
            if percen <= 75:
                color = (0, 255, 0) # green, use 40-75 %
            elif percen <= 83:
                color = (255, 255, 0) # yellow, use 75-83 %
            elif percen <= 91:
                color = (0, 128, 255) # blue, use 83-91 %
            else:
                color = (255, 0, 0) # red, use > 91 %
            
            leds = [1, 2]
            # turn on leds
            
            t1 = threading.Timer(led_on_after, self.hat.set_led_color, [color, leds])
            t1.start()
            
        
        # turn off leds after 5 sec
        t2 = threading.Timer(led_off_after, self.hat.set_led_color, [(0, 0, 0)])
        t2.start()
    
    
    def send_message(self, message, usb_type=True, ack_need=True):
        # send message to the Ardu
        
        if usb_type:
            if self.serial is None:
                logging.debug("Error: No USB connection with Ardu!")
                return False
            bytes_ = self.serial.write(message + '\n')
            time.sleep(0.2)
            
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
                    answ = answ.translate(None, chr(10)+chr(13))
                    logging.debug("Got msg from TCP/IP client: "+ answ)
                    
                if answ == 'ack':
                    return True
                
                # sleep
                time.sleep(0.3)
                
                n += 1
            
            return False # if no 'ack' recieved during 3 trials
        else: # counts bytes sent
            if bytes_ == len(message) + 1:
                return True
            else:
                return False

    
    def reset_arduino(self):
        # reset arduino
        
        return self.send_message('reset')
    
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
            self.reset_arduino()
            if res:
                self.ardu_maint_mode = True
                self.rpi_maint_mode = True
                self.time_synchronized = False
            
                # pause sensing threads on the rpi
                for sense_thread in self.sense_threads:
                    sense_thread.m_pause(sense_thread.getName())
                    while not sense_thread.m_paused():
                        time.sleep(0.05)
#                    logging.debug("Paused")
                
                return True
            return False
                    
        else:
            # synh time from the host
            if self.rpi_maint_mode and self.time_synchronized:
            
                # disable Ardu maint mode
                self.reset_arduino()
                res = self.set_ardu_mode('run')
                
                if res:
                    self.ardu_maint_mode = False
                    self.rpi_maint_mode = False
                    
                    # resume all paused threads
                    for sense_thread in self.sense_threads:

                        for t in threading.enumerate():
                            if t.getName() == sense_thread.getName():
                               t.m_reset_pause(t.getName())
                               time.sleep(0.5)
                             
                    
                    return True
                return False
            
        
    def read_tcp_data(self):
        # reads data from the TCP port
        
        try:
#            logging.debug("Reading TCP data, timeout is " + str(self.conn.gettimeout()))
            data = self.conn.recv(1024)
            if not data:
                logging.debug("TCP/IP connection loses.") 
                self.conn = None
                return None
        except sc.timeout:
#            logging.debug("TCP/IP connection timeout.") 
            return None
        except sc.error:
            logging.debug("TCP/IP connection loses.") 
            self.conn = None
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
                self.socket.listen(5)
                self.conn, addr = self.socket.accept()
                logging.debug("Connected with TCP client from {:s} adress.".format(addr))
                self.conn.settimeout(self.time_out_tcp)
                self.send_message('Hi!\nPlease, type a command >', usb_type=False, ack_need=False)
#                self.socket.setblocking(0)
            except sc.timeout as e:
                return False
        else:
            return True
    
    def read_usb_data(self):
        # reads data from the usb port
        
        usb_data = ''

        while self.serial.inWaiting() > 0:
            byte_ = self.serial.read(1)
            if ord(byte_) == 13:
                break
            else:
                usb_data += byte_
        
        usb_data = usb_data.translate(None, chr(10)+chr(13))
        
        return usb_data
    
    def get_messages(self):
        # get messages from the USB or TCP port and switch data flow
        
        t1 = time.time()
        
        while True:
            # read USB data
            if self.m_stopped():
                break

            usb_line = self.read_usb_data()
            time.sleep(0.05)
#            logging.debug("Data from USB: " + usb_line)
#            for usb_line in usb_data:
                
            if len(usb_line) > 0:
                
                logging.debug("Got msg from USB: " + usb_line + ":len=" + str(len(usb_line)))
                # send RPI time to Ardu
                if usb_line == 'curr_time' and len('curr_time') == len(usb_line):
#                    logging.debug("Processiong curr_time")
                    self.send_message('ack', ack_need=False)
                    self.get_current_time()
                    
                if usb_line == 'trigger_time':
                    self.send_message('ack', ack_need=False)
#                    wake_, down_, in_between = self.calendar.get_sleep_up_time(in_epoch = True)
                    
                    if self.scheduled_shutdown:
                        self.prepare_to_shutdown_rpi()
                    else:
                        self.setup_triggers()
                    

                if usb_line == 'current_status':
                    self.set_user_activity()
                    
                    self.send_message('ack', ack_need=False)
                    self.show_rpi_status()
                    
                    
                if usb_line == 'shutdown' or usb_line == 'shutdownusr':
                    if usb_line == 'shutdownusr':
                        self.beep_on = True
                    else:
                        self.beep_on = False
                        
                    self.send_message('ack', ack_need=False)
                    self.scheduled_shutdown = True
                    
#                    self.prepare_to_shutdown_rpi()               
                    
                
                if usb_line.find('curr_time') == 0 and len(usb_line) > 11 and not self.time_synchronized:
                    self.send_message('ack', ack_need=False)
                    self.set_current_time(long(usb_line[10:]))
                    if self.rpi_maint_mode:
                        # resume all paused threads
                        for sense_thread in self.sense_threads:
                            for t in threading.enumerate():
                                if t.getName() == sense_thread.getName():
                                   t.m_reset_pause(t.getName())
                                   time.sleep(0.5)
                        self.rpi_maint_mode = False
                        self.ardu_maint_mode = False
                    
            
            # read TCP data
            if self.listen_tcp_client():
                tcp_data = self.read_tcp_data()
                
                if tcp_data is not None and len(tcp_data) > 0:
                    # close connection by the client request
                
                    logging.debug("Got msg from TCP/IP client: " + tcp_data)
                    if tcp_data == 'logout':
                        self.set_user_activity()
                        self.conn.close()
                        self.conn = None
                        
                    
                    # synch time from the host computer
                    if tcp_data.find("time_synch") >=0:
                        self.set_user_activity()
                        try:
                            time_epoch = long(tcp_data[tcp_data.find("time_synch") + 11:])
                            
                            time_set_res = self.set_current_time(time_epoch)
                            

                            if time_set_res:
                                self.send_message('ack', usb_type=False, ack_need=False)
                                self.show_rpi_status()
                            
                        except:
                            self.send_message('Something wrong with the time epoch', usb_type=False, ack_need=False)
                    
                    # delete all frames and log files
                    if tcp_data == 'clean_rpi':
                        self.set_user_activity()
                        res = self.clear_rpi()
                        if res:
                            self.send_message('done', usb_type=False, ack_need=False)
                        else:
                            self.send_message('ack', usb_type=False, ack_need=False)
                        
                    # get available space on rpi SD
                    if tcp_data == 'memory':
                        bytes_, percen = self.shell.get_memory_available()
                        self.send_message(str(bytes_), usb_type=False, ack_need=False)
                        
                        self.set_user_activity()
                        self.show_rpi_status()
                    
                    # shutdown rpi 
                    if tcp_data == 'shutdown':
                        
                        self.send_message('ack', usb_type=False, ack_need=False)
                        self.shutdown_rpi(force=True)
                        
                    # enable maintenance mode for the rpi
                    if tcp_data == 'enable_maint':
                        self.set_user_activity()
                        res = self.set_maint_mode(True)
                        if res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                        
                        
                    # disable maintenance mode for the rpi
                    if tcp_data == 'disable_maint':
                        self.set_user_activity()
                        res = self.set_maint_mode(False)
                        if res:
                            self.send_message('ack', usb_type=False, ack_need=False)
                            
                        
                        

                    # disable maintenance mode for the rpi and shutdown rpi
                    if tcp_data == 'disable_maint&shutdown':
                        res = self.send_message('ack', usb_type=False, ack_need=False)
                        if res:
                            self.set_maint_mode(False)
                            self.scheduled_shutdown = True
#                            time.sleep(2.0)
#                            continue
                        
                        

                            
                    if tcp_data == 'curr_time':
                        self.set_user_activity()
                        self.send_message('ack')
                        
                        
                    if tcp_data == 'astatus':
                        self.set_user_activity()
                        self.send_message('status', usb_type=True, ack_need=False)
                        self.show_rpi_status()
                    
                    if tcp_data == 'uptimes':
                        self.set_user_activity()
                        self.send_message('ack', usb_type=False, ack_need=False)

                        wake_, down_, _ = self.calendar.get_sleep_up_time(in_epoch = True)
                        logging.debug("Wakeup time UTC epoch: {:d}, down time: {:d}".format(wake_, down_))
                        
                        wake_, down_, _ = self.calendar.get_sleep_up_time(in_epoch = False)
                        logging.debug("Wakeup time LOCAL: {:s}, down time: {:s}".format(str(wake_), str(down_)))
                    
                    if tcp_data == 'calendar':
                        self.set_user_activity()
                        self.send_message('ack', usb_type=False, ack_need=False)
                        for on, off in self.calendar.up_event_times:
                            logging.debug(str(on) + " " + str(off))
            
            if self.user_activity is not None and not self.rpi_maint_mode:
                if self.get_user_last_activity_tinterval() >= 10 * 60.0:
                    logging.debug("Self autoshutdown started")
                    self.user_activity = None
                    self.prepare_to_shutdown_rpi()
#                self.scheduled_shutdown = 'run'
            
            # get time from Arduino if Arduino's time is synchronized
            if not self.time_synchronized and time.time() - t1 >= 5.0:
                self.send_message('get_ardu_time')
                t1 = time.time()
            
            if self.scheduled_shutdown == 'run':
                self.scheduled_shutdown = False
                
                self.shutdown_rpi(force=False)

                    
        
    
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
    def __init__(self, root_path, index=''):
        # class's constructor
    
        super(MyBuffer, self).__init__()
        self.stack = []
        self.index = index
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
#            if len(vals) == 3:
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
        dir_path = join(self.root_path, "dump_{:d}_{:s}_{:s}".format(max_id, date.strftime('%d.%m.%Y'), self.index))
        makedirs(dir_path)
        
        # set permissions
        new_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        os.chmod(dir_path, new_mode)
            
        return dir_path
        
        
    
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
                 framerate=12, resolution=(800, 600), sleep_time=15.0, rotation=90):
        super(Camera_capture, self).__init__()
#        threading.Thread.__init__(self)
        self.name = name
        self.path_to_save = path_to_save
        self.framerate = framerate
        self.resolution = resolution
        self.rot = rotation
        
        self.counter = counter
        self.sleep_time = sleep_time
        self.storage = storage_thread
        logging.debug("Camera thread initialized")
        self.paused = False
        

    def run(self):
        # enter point in the Thread
        
        if not exists(self.path_to_save):
            makedirs(self.path_to_save)
            new_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
            os.chmod(self.path_to_save, new_mode)
    
        if self.m_paused():
            logging.debug("Starting in paused mode")
        else:
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
                time.sleep(0.1)
                continue
            
            camera = PiCamera()
            time.sleep(prep_time)
            camera.framerate = self.framerate
            camera.resolution = self.resolution
            camera.rotation = self.rot
            file_name = join(self.path_to_save, 'img{:05d}.jpg'.format(self.counter))
            camera.capture(file_name, format='jpeg', quality = 70)
            
            # set file permissions
            new_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
            os.chmod(file_name, new_mode)
            
            logging.debug("Camera capture") 
            camera.close()
            self.storage.push_data({'image': self.counter, 'time': time.time()})
            time.sleep(abs(self.sleep_time - prep_time))
            self.counter += 1
    
    
        

class Data_storage(object):
    # class for data gathering from different sensors and saving in files
    
    def __init__(self, path_root, index=''):
        super(Data_storage, self).__init__()
        self.buffer = MyBuffer(path_root, index)
        self.dump_path = self.buffer.get_current_dump_dir()
    
    def push_data(self, data):
        # push data dictionary in the buffer
        self.buffer.push_value(data)
        
    def delete_all_data(self):
        # delete all files except current dump dir in the Rpi data storage
        
        # delete all items from a root path
        all_items = [item for item in listdir(self.buffer.root_path)]
        logging.debug("Deleting all files in the {:s}".format(self.buffer.root_path))
        time.sleep(1.0)
        try:
            for item_ in all_items:
                # delete item
                full_path = join(self.buffer.root_path, item_)
                
                if self.dump_path == full_path:
                    continue
                
                logging.debug("Deleting " + full_path)
                if isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
                logging.debug("Deleted " + full_path)
                    
        except:
            logging.debug("Error in log files deletion.")
            return False
        
        return True
        
class Calendar(object):
    # class for sleep and wakeup time management
    
    def __init__(self):
        super(Calendar, self).__init__()
        self.up_event_times = []
        
        
    
    def load_calendar_from_file(self, file_name):
        # loads calendar from txt file
    
        f = open(file_name, 'r')
        data = f.read()
        f.close()
        
        counter = 0
        
        for line in data.split('\n'):
            
            # ignoring lines with #
            if line.find('#') >= 0:
                continue
            
            try:
                line = line.translate(None, chr(10)+chr(13))
                
                if len(line) == 0:
                    continue
                
                date_s, on_s, off_s = line.split(' ')
    
                # prepare rpiup event times
                self.add_item(date_s, on_s, off_s)
                
            except:
                logging.debug("Calendar's line was ignored: {:s}".format(line))
                continue            

            counter += 2
        
        logging.debug("Calendar: loaded {:d} records.".format(counter))
            
    
    def add_item(self, date_s, time_on_s, time_off_s):
        # adds new Item to the calendar
        
        on_time = datetime.datetime.strptime(date_s + time_on_s, '%d.%m.%Y%H:%M')
        off_time = datetime.datetime.strptime(date_s + time_off_s, '%d.%m.%Y%H:%M')
        
        self.up_event_times.append((on_time, off_time))

    def get_nearest_up_time(self):
        
        if len(self.up_event_times) == 0:
            logging.debug("Calendar is not loaded")
            return None
        
        
        curr_time = datetime.datetime.now()
        nearest_diff = None
        nearest = None
        
        for uptime, downtime in self.up_event_times:
#            logging.debug("Processing: " + str(uptime))
            if (curr_time >= uptime + datetime.timedelta(seconds = 30) and curr_time < downtime - datetime.timedelta(seconds = 30)):
                nearest = (uptime, downtime)
                break
        
            if uptime > curr_time:
                diff = uptime - curr_time
                
                if diff.total_seconds() < nearest_diff or nearest_diff is None:
                    nearest_diff = diff.total_seconds()
                    nearest = (uptime, downtime)
                    
        return nearest
        
    def date2epoch(self, date_obj):
        # converts datetime object into time epoch
    
        unix_time_start = datetime.datetime.strptime('01-01-1970', '%d-%m-%Y')
        diff = date_obj - unix_time_start
        
        return int(diff.total_seconds() + time.timezone)
    
    def get_sleep_up_time(self, in_epoch = True):
        # returns the next nearest wakeup and sleep time
    
        up_time, down_time = self.get_nearest_up_time()
#        logging.debug("Nearest time found: UP{:s}, down{:s}".format(str(up_time), str(down_time)))
        
        t_now = datetime.datetime.now()

        
        
        intersect = False
        if t_now >= up_time - datetime.timedelta(seconds = 30) and t_now + datetime.timedelta(seconds = 30) < down_time:
            intersect = True
        
        if in_epoch:
            return self.date2epoch(up_time), self.date2epoch(down_time), intersect
        else:
            return up_time, down_time, intersect

class HostPC(threading.Thread):
    # class for data copying fro the rpi in the local folder

    port = 5500
    
    def __init__(self, local_folder = '/home/hrpi/data_sync', rpi_ip = '192.168.0.5'):
        super(HostPC, self).__init__()
        
        self.name = 'HostPC'
#        self.socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
#        
#        self.time_out_tcp = 0.01
#        self.socket.settimeout(self.time_out_tcp)        
        self.rpi_ip = rpi_ip
        self.rpi_names  = ['rpiA', 'rpiB'] # ssh aliases defined in the config file of .ssh dir on the host
#        self.socket.bind((self.rpi_ip, self.port))
        
        self.conn = None
        self.shell = Shell_executer()
        self.local_folder = join(local_folder, 'logdata')
        self.update_folder = join(local_folder, 'update')


    def check_last_dir(self):
        # check the last dump directory in the root path and creates one new
        
        # get list with directories in the root
        dirnames_all = [dirname for dirname in listdir(self.local_folder) if isdir(join(self.local_folder, dirname))]
        
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
        dir_path = join(self.local_folder, "data_{:d}_{:s}".format(max_id, date.strftime('%d.%m.%Y')))
        makedirs(dir_path)
        
        # set permissions
        new_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        os.chmod(dir_path, new_mode)
            
        return dir_path
    
    def get_data_from_rpi(self, save_to, files = ''):
        
        for name in self.rpi_names:
            res = self.shell.copy_files_via_ssh(name, files, save_to,  from_user = 'pi')
            if res:
                break
        
        return res
    
    def check_for_update(self):
        
        # check if any files need to be updated on the host and rpi
        files_all = [file_name for file_name in listdir(self.update_folder) if isfile(join(self.update_folder, file_name))]
        if len(files_all) > 0:
            return True
        else:
            return False
    
    def beep(self, seconds=1.0):
        
        duration = seconds  # second
        freq = 440  # Hz
        os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % (duration, freq))
    
    def update_rpi(self):
            
        if self.check_for_update():
            # update the RPI
            save_to = '/home/pi/hdeer'
            
            for name in self.rpi_names:
                res1 = self.shell.copy_files_via_ssh(name, join(self.update_folder, '*.*'), save_to,  to_user = 'pi')
                if res1:
                    break
            
            if not res1:
                logging.debug("Error: updating rpi")
                return False
        
            # update host
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            res1 = self.shell.run('cp ' + join(self.update_folder, '*.py') + ' ' + curr_dir)
            
            if not res1:
                logging.debug("Error: updating host")
                return False

        return True
        
            
    
#    def get_logs_from_rpi(self, save_to):
        
#        return self.shell.copy_files_via_ssh(self.rpi_ip, '/home/pi/hdeer/hdeer.log', save_to,  from_user = 'pi')

    def send_message(self, message, ack_need=True, ack_msg = 'ack'):
        # send message to the Ardu

#        if self.conn is None:
#            logging.debug("Error: No TCP connection with Host!")
#            return False
            
        bytes_ = self.socket.send(message + '\n')            
        logging.debug("Sent msg to the rpi: "+ message)
            
        if ack_need:
                  
            # try to send message
            t1 = time.time()            
            while time.time() - t1 <= 60: # try 3 times
            
                if int(time.time() - t1) % 10 == 0:      
                    bytes_ = self.socket.send(message + '\n')            
                    logging.debug("Next try: sent msg to the rpi: "+ message)
                    time.sleep(0.8)

                answ = self.read_tcp_data()
                if answ == '' or answ is None:
                    time.sleep(1.0)
                    continue
                answ = answ.translate(None, chr(10)+chr(13))
                logging.debug("Got msg from TCP/IP client: "+ answ)
                    
                if answ == ack_msg:
                    return True
                
                # sleep
                time.sleep(1.0)
            
            return False # if no 'ack' recieved during 3 trials
        else: # counts bytes sent
            if bytes_ == len(message) + 1:
                return True
            else:
                return False


    def read_tcp_data(self):
        # reads data from the TCP port
        
        try:
            data = self.socket.recv(1024)
            if not data:
                logging.debug("TCP/IP connection loses.") 
#                self.conn = None
                return None
        except sc.timeout:
            return None
        except sc.error:
            logging.debug("TCP/IP connection loses.") 
#            self.conn = None
            return None
        except:
            return None
        
        # ignore \n or \r symbols
        line = ''
        for byte in data:
            if not(ord(byte) == 13 or ord(byte) == 10):
                line += byte
            else:
                return line
        
        return line
    
    def run(self):
        logging.debug("Running..")
        
        self.socket = sc.socket(sc.AF_INET, sc.SOCK_STREAM)
        self.time_out_tcp = 0.2
        self.socket.settimeout(self.time_out_tcp)
        while True:         
            try:
                
                    
                self.socket.connect((self.rpi_ip, self.port))
#            except sc.timeout as e:
#                logging.debug("Connection timeout.")
#                time.sleep(1.0)
#                continue
            except sc.error as e1:
#                logging.debug("Can't connect to the rpi: " + str(e1))
#                time.sleep(0.01)
                continue
            
            logging.debug('Connected to the rpi!')
            time.sleep(1.0)
            _ = self.read_tcp_data()
#            _ = self.read_tcp_data()
#            _ = self.read_tcp_data()
            
            if self.send_message('enable_maint'):
                logging.debug("Enable rpi & ardu maint - OK")
            else:
                logging.debug("Enable rpi & ardu maint - FAILED")
                break
            time.sleep(2.0)
                
            new_folder = self.check_last_dir()
            to_path = join(self.local_folder, new_folder)
            
            if self.get_data_from_rpi(to_path, files='/home/pi/sources/data/*.*'):
                logging.debug("All files were coppied from the rpi - OK")
            else:
                logging.debug("All files were coppied from the rpi - FAILED")
                break
 
            
            
            time.sleep(1.0)
            if self.send_message('clean_rpi', ack_msg='done'):
                logging.debug("The rpi cleaned up - OK")
            else:
                logging.debug("The rpi cleaned up - FAILED")
                break
            
            time.sleep(1.0)
            if self.check_for_update():
                if self.update_rpi():
                    logging.debug("The rpi and host update - OK")
                else:
                    logging.debug("The rpi and host update - FAILED")
                    break
            else:
                logging.debug("The rpi and host update - nothing to update")
            
            time.sleep(1.0)
            epoch = self.shell.get_system_time_epoch()            
            if self.send_message('time_synch:{:d}'.format(epoch)):
                logging.debug("Time is synchronized - OK")
            else:
                logging.debug("Time is synchronized - FAILED")
                break
            
            to_path_log = join(to_path, 'hdeer.log')
            if self.get_data_from_rpi(to_path_log, files='/home/pi/hdeer/hdeer.log'):
                logging.debug("The log file was coppied from the rpi - OK")
            else:
                logging.debug("The log file was coppied from the rpi - FAILED")
                break
            
            time.sleep(1.0)
            if self.send_message('disable_maint&shutdown'):
                logging.debug("Maintenance mode was disabled for the rpi and ardu - OK")
            else:
                logging.debug("Maintenance mode was disabled for the rpi and ardu - FAILED")
                break
            
            if self.send_message('logout', ack_need=False):
                logging.debug("Logout - OK")
                self.socket.close()
            else:
                logging.debug("Logout - FAILED")
            
            logging.debug("Data synch is done!!!")
            
            self.beep()
            time.sleep(0.5)
            self.beep()
            logging.debug("Exiting")
#            self.shell.shutdown()
            
            return True
            
            break
        
#        return True
    
        # try to restore RPI
        epoch = self.shell.get_system_time_epoch()            
        if self.send_message('time_synch:{:d}'.format(epoch)):
            logging.debug("Restore: time is synchronized - OK")
        else:
            logging.debug("Restore time is synchronized - FAILED")
        
        time.sleep(2.0)
        if self.send_message('disable_maint'):
            logging.debug("Restore: maint disabled - OK")
        else:
            logging.debug("Restore: maint disabled - FAILED")
        
        self.socket.close()
        logging.debug("Conncetion closed")
        logging.debug("Exiting")
        
        return False
            
            

                
    