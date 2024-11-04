#!/usr/bin/env python3
import pymoos
import time
import sys
import numpy as np
import socket
import pybuzz
from MoosReader import MoosReader
from threading import Event



class Ship(pymoos.comms):

    def __init__(self, params):
        """Initiates MOOSComms, sets the callbacks and runs the loop"""
        super(Ship, self).__init__()
        self.server = 'localhost'
        self.port = int(params['ServerPort'])
        self.name = 'iSMH'

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
        

        self.pid = 'moos'
        self.server_addr = '172.16.11.38'
        #self.db_conn_str = 'mongodb://172.16.11.10:27017'
        self.db_conn_str = 'mongodb://10.1.1.54:27017'
        self.db_name = 'smh'
        self.ds = pybuzz.create_bson_data_source(self.db_conn_str, self.db_name)
        self.session = pybuzz.join_simco_session(self.pid, pybuzz.create_bson_serializer(self.ds))
        self.session.initialize()
        self.session.is_publisher(pybuzz.rudder_tag(), pybuzz.rudder_tag.SMH_DEMANDED_ANGLE)
        self.session.is_publisher(pybuzz.thruster_tag(), pybuzz.thruster_tag.SMH_DEMANDED_ROTATION)
        self.ready = Event()
        self.session.connect(self.server_addr)
        self.ready.wait()
        self.vessel = self.session.vessels['']


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

    def receiveSHM(self):
        #pass
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

    def debug(self):
        # print(f"REAL X = {self.real_x}")
        # print(f"REAL Y = {self.real_y}")
        # print(f"REAL HEADING = {self.real_heading}")
        # print(f"REAL SPEED = {self.real_speed}")
        # print(f"DESIRED ROTATION = {self.desired_rotation}")
        # print(f"DESIRED RUDDER = {self.desired_rudder}")
        if len(self.session.vessels)>0:
            self.session.sync(self.session.vessels[0])
            print(self.session.vessels[0].linear_velocity[0])
            self.session.vessels[0].thrusters[0].dem_rotation = 15
            self.session.vessels[0].thrusters[1].dem_rotation = 15
            self.session.sync(self.session.vessels[0])
            

    def iterate(self):
        while True:
            self.updateTPN()
            self.receiveSHM()
            self.updateMOOS()
            self.debug()

    def on_state_changed(self, state):
         # write code to run when the simulation starts
         if state == pybuzz.RUNNING:
             print('Simulation is running!')
             self.ready.set()

        
if __name__ == "__main__":
    # try:
    file = sys.argv[1] 
    params = MoosReader(file,"iPydyna")
    ship = Ship(params)
    ship.iterate()
    # except:
    #     for e in sys.exc_info():
    #         print(e)
