#!/usr/bin/env python3
import pymoos
import time
import numpy as np

class myPID:

    def __init__(self, Kp, Ki, Kd, dt, max_output):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.max_output = max_output

        self.setpoint = 0
        self.int_err = 0
        self.prev_err = 0
        # self.prev_y = 0
        self.saturated = 0

    def output(self, y):
        error = self.setpoint - y
        diff_error = (error - self.prev_err) / self.dt
        # diff_error = (y - self.prev_y) / self.dt
        self.int_err += error * self.dt
        output = self.Kp * error + (1-self.saturated) * self.Ki * self.int_err + self.Kd * diff_error
        if abs(output) > self.max_output:
            output = output/abs(output)*self.max_output
            self.saturated = 1
            self.int_err = 0
        else:
            self.saturated = 0
        self.prev_err = error
        # self.prev_y = y
        return output

class pTrajectPID(pymoos.comms):

    def __init__(self, moos_community, moos_port):
        """Initiates MOOSComms, sets the callbacks and runs the loop"""
        super(pTrajectPID, self).__init__()
        self.server = moos_community
        self.port = moos_port
        self.name = 'pTrajectPID'

        self.set_on_connect_callback(self.__on_connect)
        self.set_on_mail_callback(self.__on_new_mail)

        self.add_active_queue('desired_queue', self.on_desired_message)
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_SPEED')
        self.add_message_route_to_active_queue('desired_queue', 'DESIRED_HEADING')

        self.add_active_queue('sensor_queue', self.on_sensor_message)
        self.add_message_route_to_active_queue('sensor_queue', 'SENSOR_SPEED')
        self.add_message_route_to_active_queue('sensor_queue', 'SENSOR_HEADING')

        self.add_active_queue('ivphelm_queue', self.on_ivphelm_message)
        self.add_message_route_to_active_queue('ivphelm_queue', 'IVPHELM_ALLSTOP')
        self.manual="false"
        
        self.desired_speed = 0
        self.desired_heading = 0

        self.sensor_speed = 0
        self.sensor_heading = 0

        self.desired_rudder = 0
        self.desired_rotation = 0

        self.run(self.server, self.port, self.name)
        pymoos.set_moos_timewarp(10)
        self.dt=0.1

        dt=self.dt/3
        # self.speedPID = myPID(Kp=4.944*4, Ki=0.1629*4, Kd=0, dt=dt, max_output=17.5)
        self.speedPID = myPID(Kp=4.944*2, Ki=0.1629*5, Kd=0, dt=dt, max_output=17.5)
        self.coursePID = myPID(Kp=3.97, Ki=0.269, Kd=3.95, dt=dt, max_output=35)


    def __on_connect(self):
        """OnConnect callback"""
        print("Connected to", self.server, self.port,
              "under the name ", self.name)
        return (self.register('DESIRED_SPEED', 0) and
                self.register('DESIRED_HEADING', 0) and
                self.register('SENSOR_SPEED', 0) and
                self.register('SENSOR_HEADING', 0) and
                self.register('IVPHELM_ALLSTOP', 0))

    def __on_new_mail(self):
        """OnNewMail callback"""
        for msg in self.fetch():
            pass
        return True

    def on_desired_message(self, msg):
        """Special callback for Desired"""
        if msg.key() == 'DESIRED_SPEED':
            self.desired_speed = msg.double() # m/s
        elif msg.key() == 'DESIRED_HEADING':
            self.desired_heading = msg.double() # graus
        return True

    def on_sensor_message(self, msg):
        """Special callback for Sensor"""
        if msg.key() == 'SENSOR_SPEED':
            self.sensor_speed = msg.double() # m/s
        elif msg.key() == 'SENSOR_HEADING':
            self.sensor_heading = msg.double() # graus
        return True

    def on_ivphelm_message(self, msg):
        """Special callback for Ivphelm"""
        if msg.key() == 'IVPHELM_ALLSTOP':
            self.manual = msg.string()
        return True


    def send(self, key, value):
        self.notify(key, value, -1)

    def update(self):
        self.send('DESIRED_RUDDER', self.desired_rudder)
        self.send('DESIRED_ROTATION', self.desired_rotation)

    def debug(self, dt):
        print(" ")
        print(" ")
        print(" ")
        print("pTrajectPID Debug")
        print(f"Manual= {self.manual}")


    def iterate(self):
        dt = self.dt
        dt_fast_time = dt/pymoos.get_moos_timewarp()
        while True:
            time.sleep(dt_fast_time)
            print(f"Manual= {self.manual}")
           
            # Atualiza setpoint
            if self.manual!="ManualOverride":
                self.speedPID.setpoint = self.desired_speed
                heading_diff = self.desired_heading - self.sensor_heading
                if heading_diff >= 180:
                    self.coursePID.setpoint = self.desired_heading - 360
                elif heading_diff <= -180:
                    self.coursePID.setpoint = self.desired_heading + 360
                else:
                    self.coursePID.setpoint = self.desired_heading

                # Atualiza atuadores
                self.desired_rotation = self.speedPID.output(self.sensor_speed)
                self.desired_rudder = self.coursePID.output(self.sensor_heading)

                self.update()
            self.debug(dt)


def main():
    PIDcontrol = pTrajectPID('localhost', 9000)
    PIDcontrol.iterate()


if __name__ == "__main__":
    main()
