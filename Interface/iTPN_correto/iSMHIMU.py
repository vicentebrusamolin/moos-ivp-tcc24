#!/usr/bin/env python3
import pymoos
import time
import sys
import numpy as np
import socket
import pybuzz
from MoosReader import MoosReader
from threading import Event
from numpy import cos, sin, deg2rad



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
        self.dt = 0.1
        
        #CODESIM
        self.pid = '2030'
        self.server_addr = '10.1.1.92' 
        self.db_conn_str = 'mongodb://10.1.1.54:27017'
        
        #ALPHA
        #self.pid = '911'
        #self.server_addr = '172.16.11.38'	
        #self.db_conn_str = 'mongodb://10.1.1.54:27017'
        
        self.db_name = 'smh'
        self.ds = pybuzz.create_bson_data_source(self.db_conn_str, self.db_name)
        self.session = pybuzz.join_simco_session(self.pid, pybuzz.create_bson_serializer(self.ds))
        self.session.initialize()
        self.session.is_publisher(pybuzz.rudder_tag(), pybuzz.rudder_tag.SMH_DEMANDED_ANGLE)
        self.session.is_publisher(pybuzz.thruster_tag(), pybuzz.thruster_tag.SMH_DEMANDED_ROTATION)
        # self.ready = Event()
        self.session.connect(self.server_addr)
        self.navio = []
        # self.ready.wait()


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

    def updateMOOS(self):
        # to MOOS
        self.sendMOSS('NAV_SPEED', self.real_speed)
        self.sendMOSS('NAV_HEADING', self.real_heading)
        self.sendMOSS('NAV_X', self.real_x)
        self.sendMOSS('NAV_Y', self.real_y)
        self.sendMOSS('NAV_Z', self.real_z)
        self.sendMOSS('IMU_ROLL', self.roll_)
        self.sendMOSS('IMU_PITCH', self.pitch_)


    # def calculate_heading(self,yaw):
    #     real_heading = 0print(self.navio)
    #     i = 0
    #     j = 0
    #     real_heading = 90 - np.rad2deg(yaw)
    #     if real_heading < 0:
    #         i = abs(real_heading) // 360 + 1
    #         real_heading += 360*i
    #     if real_heading > 360:
    #         j = abs(real_heading) // 360
    #         real_heading -= 360*j
    #     return real_heading

    def receiveSHM(self):
        self.session.sync(self.navio)
        self.real_x = self.navio.linear_position[0] - 100
        self.real_y = self.navio.linear_position[1] + 200
        self.real_z = self.navio.linear_position[2]
        self.real_heading = self.navio.angular_position[2]
        yaw=-deg2rad(self.real_heading)
        self.real_speed = self.navio.linear_velocity[0]*cos(yaw)-self.navio.linear_velocity[0]*sin(yaw)
        self.roll_ = self.navio.angular_position[0]	#degrees
        self.pitch_ = self.navio.angular_position[1]	#degrees

    def updateSMH(self):    
        # to SMH
        # print(self.desired_rudder)
        self.session.vessels[0].thrusters[0].dem_rotation = self.desired_rotation*60 # self.session.vessels[0].thrusters[0].max_rotation
        self.session.sync(self.session.vessels[0].thrusters[0])
        self.session.vessels[0].thrusters[1].dem_rotation = self.desired_rotation*60 # self.session.vessels[0].thrusters[1].max_rotation
        self.session.sync(self.session.vessels[0].thrusters[1])
        self.session.vessels[0].rudders[0].dem_angle = -self.desired_rudder
        self.session.sync(self.session.vessels[0].rudders[0])
        self.session.vessels[0].rudders[1].dem_angle = -self.desired_rudder
        self.session.sync(self.session.vessels[0].rudders[1])

    def debug(self):
        print(f"REAL X = {self.real_x}")
        print(f"REAL Y = {self.real_y}")
        print(f"REAL HEADING = {self.real_heading}")
        print(f"REAL SPEED = {self.real_speed}")
        print(f"DESIRED ROTATION = {self.desired_rotation}")
        print(f"DESIRED RUDDER = {self.desired_rudder}")
        if len(self.session.vessels)>0:
            self.session.sync(self.session.vessels[0])
            # print(self.session.vessels[0].linear_velocity[0])
            print(self.session.vessels[0].linear_velocity[0])
            print(self.navio.linear_velocity[0])
            print(self.navio.linear_position[0])
            print(self.navio.angular_position[2])
            print(self.session.vessels[0].rudders[0].dem_angle)
            print(self.session.vessels[0].thrusters[0].dem_rotation)
        #     self.session.vessels[0].thrusters[0].dem_rotation = self.session.vessels[0].thrusters[0].max_rotation
        #     self.session.sync(self.session.vessels[0].thrusters[0])
        #     self.session.vessels[0].thrusters[1].dem_rotation = self.session.vessels[0].thrusters[1].max_rotation
        #     self.session.sync(self.session.vessels[0].thrusters[1])
        pass    

    def iterate(self):
        print("entrou no iterate do iSMH")
        dt = self.dt
        dt_fast_time = dt/pymoos.get_moos_timewarp()
        while True:
            #print(self.session.initialize())
            #print(self.session.connect('10.1.1.92'))
            print(self.navio)
            print(self.session.vessels)
            time.sleep(dt_fast_time)
            if len(self.session.vessels)>0:
                self.navio = self.session.vessels[0]
            if self.navio:
                try:
                    print("entrou no TRY do ITERATE")
                    self.receiveSHM()
                    self.updateMOOS()
                    self.updateSMH()
                except pybuzz.exception as e:
                    print (e)
                except:
                    for e in sys.exc_info():
                        print(e)
            self.debug()

2
2
2
2
2
2
    #    if state == pybuzz.RUNNING:
    #        print('Simulation is running!')
    #        self.ready.set()

        
if __name__ == "__main__":
    # try:
    file = sys.argv[1] 
    params = MoosReader(file,"iPydyna")
    ship = Ship(params)
    ship.iterate()
    # except:
    #     for e in sys.exc_info():
    #         print(e)
