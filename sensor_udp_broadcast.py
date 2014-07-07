#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on July 7, 2014
python serial data collector
@author: fabian@projektil.ch

s: save values to file
r: reload saved values
'''

import os, time, serial, socket

#############################################################

def scan_for_arduino():
  """scans for serial devices that match the arduino device name we´re after""" 
  # scan for available ports. return a list of tuples (num, name)
  available = []
  i = 0
  for device in os.listdir("/dev/"):
    if "tty.usb" in device or "ttyACM" in device:
      available.append((i, "/dev/" + device))
      i += 1
  return available

############################################################

class MovingAverage(object):
  """Super simple moving average filter implementation""" 

  def __init__(self, filtersize = 10):
    self.filtersize = filtersize
    self.values = []
  
  def filter(self, val):
    self.values.append(val)
    
    if(len(self.values) >= self.filtersize):
      self.values = self.values[1 : self.filtersize]

    sum = 0.0
    for v in self.values:
      sum += v
    return sum / float(len(self.values))
    

############################################################

class App(object):
  def __init__(self, serial_device):
    
    self.input_prefix = "analog_"
    num_inputs = 1
    self.analog_in = [0.0] * num_inputs
    self.filters = [MovingAverage() for i in range(num_inputs)]
    self.activity = [False] * num_inputs 

    self.serial = serial.Serial(serial_device, 57600)
    self.thresh_low = 10
    self.thresh_high = 80

    self.running = True
    
    self.udp_endpoint = ('<broadcast>', 11111)

    # prepare a socket for udp-broadcasting
    self.socket = socket.socket(socket.AF_INET, # Internet
                                socket.SOCK_DGRAM) # UDP

    self.socket.bind(('', 0))
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print("udp sensor broadcaster running ...\n")

  def run(self):

    while self.running:
      try:
        line = self.serial.readline() 
        ## parse the line to extract values
        self.parse_line(line) 

        # spread the ardiuno input as udp broadcast
        self.send_udp_broadcast(line) 

        #for index, val in enumerate(self.analog_in):
        #  pass
      except KeyboardInterrupt:
        print "\n->keyboard interrupt<-"
        self.running = False

    print "ciao\n" 
   
  def parse_line(self, line):
    tokens = line.split()
    #print tokens

    # number of tokens does not match, or token in wrong position
    if len(tokens) < 2 or tokens[0].find(self.input_prefix) != 0:
      return
    
    try: 
      parsed_index = int(tokens[0][len(self.input_prefix):])
      self.analog_in[parsed_index] = self.filters[parsed_index].filter(int(tokens[1]))
    except:
      print "shit happened during parsing\n"
      pass
    
  def saveValues(self):
    with open(self.config_file_name, 'w') as config_file: 
      config_file.write(json.dumps([{ 'foo' : self.bar }],
                                      sort_keys=True, indent=4))
    pass

  def send_udp_broadcast(self, line):
    # send notification via udp
    try:
      self.socket.sendto(line, self.udp_endpoint)
    except NameError:
      pass # variable was not defined
    except socket.error, msg:
      print("Got trouble sending notification via udp ({}): {}".format(str(msg[0]), msg[1]))
    except OverflowError, msg:
      print msg

  def readValues(self):
    print 'reading values'
    try:
      with open(self.config_file_name, 'r') as config_file: 
        values = json.loads(config_file.read())[0]
        #self.cannyLow = values[u'cannyLow']
    except:
      print "config file not found"

#############################################################

if __name__ == '__main__':  
  import sys
  print __doc__
  
  print "Found ports:"
  devices = scan_for_arduino() 
  for n, s in devices: print "(%d) %s" % (n,s)
  
  try:
    print "using serial device %d: %s" % (devices[0][0], devices[0][1])
    App(devices[0][1]).run()
  except:
    print "could not open serial device"

