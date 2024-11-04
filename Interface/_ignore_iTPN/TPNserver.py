#!/usr/bin/env python3
import socket
import time
import pydyna
import numpy as np
import threading

class TPNserver:
    def __init__(self):

        # Server Data
        self.data_payload = 2048 #The maximum amount of data to be received at once
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.setblocking(False)
        # self.client_address = ('192.168.0.16', 8081)
        # self.server_address = ('192.168.0.23', 8082)
        self.client_address = ('localhost', 8081)
        self.server_address = ('localhost', 8082)
        self.sock.bind(self.server_address)

        # Ship Data
        self.desired_rotation = 0
        self.desired_rudder = 0
        self.real_x = 900
        self.real_y = -900
        self.real_heading = 90
        self.real_speed = 0
        self.sim = pydyna.create_simulation("NACMM_2021.p3d")
        self.ship = self.sim.vessels['292']
        self.rudder0 = self.ship.rudders['0']
        self.rudder1 = self.ship.rudders['1']
        self.propeller0 = self.ship.thrusters['0']
        self.propeller1 = self.ship.thrusters['1']
        self.ship._set_linear_position([self.real_x, self.real_y, 0])
        if self.real_heading > 270:
            self.ship._set_angular_position([0, 0, np.deg2rad(450 - self.real_heading)])
        elif self.real_heading > 180:
            self.ship._set_angular_position([0, 0, np.deg2rad(360 - self.real_heading)])
        else:
            self.ship._set_angular_position([0, 0, np.deg2rad(90 - self.real_heading)])
        theta = self.ship.angular_position[2]
        self.ship._set_linear_velocity([self.real_speed * np.cos(theta), self.real_speed * np.sin(theta), 0])
        self.rudder0.dem_angle = - np.rad2deg(self.desired_rudder)
        self.propeller0.dem_rotation = self.desired_rotation
        self.rudder1.dem_angle = - np.rad2deg(self.desired_rudder)
        self.propeller1.dem_rotation = self.desired_rotation


    def receive(self):
        while True:
            msg, address = self.sock.recvfrom(self.data_payload)
            if msg:
                msg_decoded = msg.decode("utf-8")
                data = msg_decoded.split(' ')
                key = data[0]
                value = float(data[2])
                self.read_msg(key, value)
            
    def read_msg(self, key, value):
        if key == 'DESIRED_ROTATION':
            self.propeller0.dem_rotation = value
            self.propeller1.dem_rotation = value
        elif key == 'DESIRED_RUDDER':
            self.rudder0.dem_angle = np.deg2rad(value)
            self.rudder1.dem_angle = np.deg2rad(value)

    def sendMOOS(self, key, value):
        message = key + ' = ' + str(value)
        self.sock.sendto(message.encode('utf-8'), self.client_address)

    def updateMOOS(self):
        while True:
            #self.sendMOOS("REAL_X", self.real_x)
            #self.sendMOOS("REAL_Y", self.real_y)
            #self.sendMOOS("REAL_SPEED", self.real_speed)
            #self.sendMOOS("REAL_HEADING", self.real_heading)
            
            self.sendMOOS("NAV_X", self.real_x)
            self.sendMOOS("NAV_Y", self.real_y)
            self.sendMOOS("NAV_SPEED", self.real_speed)
            self.sendMOOS("NAV_HEADING", self.real_heading)          

    def calculate_heading(self):
        real_heading = 0
        i = 0
        j = 0
        real_yaw = self.ship.angular_position[2]
        real_heading = 90 - np.rad2deg(real_yaw)
        if real_heading < 0:
            i = abs(real_heading) // 360 + 1
            real_heading += 360*i
        if real_heading > 360:
            j = abs(real_heading) // 360
            real_heading -= 360*j
        return real_heading

    def iterate(self):
        while True:
            time.sleep(0.01)
            self.sim.step()
            self.real_speed = self.ship.linear_velocity[0]
            self.real_x = self.ship.linear_position[0]
            self.real_y = self.ship.linear_position[1]
            self.real_heading = self.calculate_heading()
            self.debug()

    def debug(self):
        print(f"REAL X = {self.real_x}")
        print(f"REAL Y = {self.real_y}")
        print(f"REAL SPEED = {self.real_speed}")
        print(f"DESIRED ROTATION 0 = {self.propeller0.dem_rotation}")
        print(f"DESIRED ROTATION 1 = {self.propeller1.dem_rotation}")
        print(f"DESIRED RUDDER 0 = {np.rad2deg(self.rudder0.dem_angle)}")
        print(f"DESIRED RUDDER 1 = {np.rad2deg(self.rudder1.dem_angle)}")


    def main(self):
        recv_thread = threading.Thread(target=self.receive, args=())
        it_thread = threading.Thread(target=self.iterate, args=())
        send_thread = threading.Thread(target=self.updateMOOS, args=())
        recv_thread.start()
        it_thread.start()
        send_thread.start()
            

if __name__=="__main__":
    server = TPNserver()
    server.main()
