#!/usr/bin/env python3
import pymoos
import pydyna
import time
import sys
import numpy as np
import socket
import threading
from MoosReader import MoosReader

class Ship(pymoos.comms):

    def __init__(self, params):
        """Initiates MOOSComms, sets the callbacks and runs the loop"""
        super(Ship, self).__init__()
        self.server = 'localhost'
        self.port = int(params['ServerPort'])
        self.name = 'iTPN'

        self.set_on_connect_callback(self.__on_connect)
        self.set_on_mail_callback(self.__on_new_mail)

        self.add_active_queue('desired_queue', self.on_desired_message)
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_ROTATION')
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_RUDDER')
        
        self.desired_rotation = 0
        self.desired_rudder = 0

        self.real_x = params['START_X']
        self.real_y = params['START_Y']
        self.real_heading = params['START_HEADING']
        self.real_speed = 0
        
        self.run(self.server, self.port, self.name)
        pymoos.set_moos_timewarp(params['MOOSTimeWarp'])

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.setblocking(False)
        # self.client_address = ('169.254.123.105', 8081)
        # self.server_address = ('169.254.78.61', 8082)
        self.client_address = ('localhost', 8081)
        self.server_address = ('localhost', 8082)
        self.sock.bind(self.client_address)
        self.data_payload = 2048 #The maximum amount of data to be received at once 


    def __on_connect(self):
        """OnConnect callback"""
        print("Connected to", self.server, self.port,
              "under the name ", self.name)
        self.notify('NAV_DEPTH', float(0), -1)
        return (self.register('DESIRED_ROTATION', 0) and
                self.register('DESIRED_RUDDER', 0))

    def __on_new_mail(self):
        """OnNewMail callback"""
        for msg in self.fetch():
            pass
        return True

    def on_desired_message(self, msg):
        """Special callback for Desired"""
        if msg.key() == 'DESIRED_ROTATION':
            self.desired_rotation = msg.double()
        elif msg.key() == 'DESIRED_RUDDER':
            self.desired_rudder = msg.double()
        return True

    def sendMOSS(self, key, value):
        self.notify(key, value, -1)

    def sendTPN(self, key, value):
        message = key + ' = ' + str(value)
        self.sock.sendto(message.encode('utf-8'), self.server_address)

    def updateMOOS(self):
        # to MOOS
        #self.sendMOSS('REAL_SPEED', self.real_speed)
        #self.sendMOSS('REAL_HEADING', self.real_heading)
        #self.sendMOSS('REAL_X', self.real_x)
        #self.sendMOSS('REAL_Y', self.real_y)
        #self.sendMOSS('NAV_SPEED', self.real_speed)
        #self.sendMOSS('NAV_HEADING', self.real_heading)
        #self.sendMOSS('NAV_X', self.real_x)
        #self.sendMOSS('NAV_Y', self.real_y)
        
        self.sendMOSS('NAV_SPEED', self.real_speed)
        self.sendMOSS('NAV_HEADING', self.real_heading)
        self.sendMOSS('NAV_X', self.real_x)
        self.sendMOSS('NAV_Y', self.real_y)
        self.sendMOSS('NAV_SPEED', self.real_speed)
        self.sendMOSS('NAV_HEADING', self.real_heading)
        self.sendMOSS('NAV_X', self.real_x)
        self.sendMOSS('NAV_Y', self.real_y)

    def updateTPN(self):    
        # to server
        self.sendTPN('DESIRED_ROTATION',self.desired_rotation)
        self.sendTPN('DESIRED_RUDDER',self.desired_rudder)

    def debug(self):
        #print(f"REAL X = {self.real_x}")
        #print(f"REAL Y = {self.real_y}")
        #print(f"REAL HEADING = {self.real_heading}")
        #print(f"REAL SPEED = {self.real_speed}")
        #print(f"DESIRED ROTATION = {self.desired_rotation}")
        #print(f"DESIRED RUDDER = {self.desired_rudder}")
        
        print(f"NAV X = {self.real_x}")
        print(f"NAV Y = {self.real_y}")
        print(f"NAV HEADING = {self.real_heading}")
        print(f"NAV SPEED = {self.real_speed}")
        print(f"DESIRED ROTATION = {self.desired_rotation}")
        print(f"DESIRED RUDDER = {self.desired_rudder}")

    def receiveTPN(self):
        try:
            msg, address = self.sock.recvfrom(self.data_payload)
            if msg:
                msg_decoded = msg.decode("utf-8")
                data = msg_decoded.split(' ')
                key = data[0]
                value = float(data[2])
                self.read_msg(key, value)
        except:
            pass
            
    def read_msg(self, key, value):
        #if key == 'REAL_X':
        #        self.real_x = value
        #elif key == 'REAL_Y':
        #        self.real_y = value
        #elif key == 'REAL_HEADING':
        #        self.real_heading = value
        #elif key == 'REAL_SPEED':
        #        self.real_speed = value
        #else:
        #    pass
            
        if key == 'NAV_X':
                self.real_x = value
        elif key == 'NAV_Y':
                self.real_y = value
        elif key == 'NAV_HEADING':
                self.real_heading = value
        elif key == 'NAV_SPEED':
                self.real_speed = value
        else:
            pass

    def iterate(self):
        while True:
            self.updateTPN()
            self.receiveTPN()
            self.updateMOOS()
            self.debug()

        
if __name__ == "__main__":
    file = sys.argv[1] 
    params = MoosReader(file,"iPydyna")
    ship = Ship(params)
    ship.iterate()
