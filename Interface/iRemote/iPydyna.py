#!/usr/bin/env python3
import pymoos
import pydyna
import time
import numpy as np
#teste

class Ship(pymoos.comms):

    def __init__(self, moos_community, moos_port):
        """Initiates MOOSComms, sets the callbacks and runs the loop"""
        super(Ship, self).__init__()
        self.server = moos_community
        self.port = moos_port
        self.name = 'iPydyna'

        self.set_on_connect_callback(self.__on_connect)
        self.set_on_mail_callback(self.__on_new_mail)

        self.add_active_queue('desired_queue', self.on_desired_message)
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_ROTATION')
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_RUDDER')
        
        self.desired_rotation = 0
        self.desired_rudder = 0

        self.real_x = 200
        self.real_y = -1900
        self.real_heading = 90
        self.real_speed = 0

        self.sim = pydyna.create_simulation("Navio_L15B4_Conv.p3d")
        self.ship = self.sim.vessels['207']
        self.rudder = self.ship.rudders['0']
        self.propeller = self.ship.thrusters['0']

        self.ship._set_linear_position([self.real_x, self.real_y, 0])
        if self.real_heading > 270:
            self.ship._set_angular_position([0, 0, np.deg2rad(450 - self.real_heading)])
        elif self.real_heading > 180:
            self.ship._set_angular_position([0, 0, np.deg2rad(360 - self.real_heading)])
        else:
            self.ship._set_angular_position([0, 0, np.deg2rad(90 - self.real_heading)])
        theta = self.ship.angular_position[2]
        self.ship._set_linear_velocity([self.real_speed * np.cos(theta), self.real_speed * np.sin(theta), 0])

        self.rudder.dem_angle = - self.desired_rudder
        self.propeller.dem_rotation = self.desired_rotation

        self.run(self.server, self.port, self.name)
        pymoos.set_moos_timewarp(10)


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

    def send(self, key, value):
        self.notify(key, value, -1)

    def update(self):
        self.send('NAV_SPEED', self.real_speed)
        self.send('NAV_HEADING', self.real_heading)
        self.send('NAV_X', self.real_x)
        self.send('NAV_Y', self.real_y)
        

    def debug(self, dt):
        print(" ")
        print(" ")
        print(" ")
        print("iPydyna Debug")
        print("Pydyna Heading", np.rad2deg(self.ship.angular_position[2]))
        # print("desired_thrust", self.desired_rotation)
        # print("desired_rudder", self.desired_rudder)
        print("dt", dt*pymoos.get_moos_timewarp())
        print(f"freq_real {1 / dt / pymoos.get_moos_timewarp()}Hz")
        print(f"freq_fast {1 / dt}Hz")

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
        dt = 0.1 # dt do p3d
        dt_fast_time = dt/pymoos.get_moos_timewarp()
        while True:
            time.sleep(dt_fast_time)

            # Atualiza leme e thrust
            self.propeller.dem_rotation = self.desired_rotation
            self.rudder.dem_angle = np.deg2rad(self.desired_rudder)

            # Calcula a iteração
            self.sim.step()
            self.real_speed = self.ship.linear_velocity[0]
            self.real_x = self.ship.linear_position[0]
            self.real_y = self.ship.linear_position[1]
            self.real_heading = self.calculate_heading()

            self.update()
            # self.debug(dt)


def main():
    ship = Ship('localhost', 9000)
    ship.iterate()
        

if __name__ == "__main__":
    main()
