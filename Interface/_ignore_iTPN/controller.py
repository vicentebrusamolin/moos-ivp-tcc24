#!/usr/bin/env python3
import pybuzz
import sys
from threading import Event

ready = Event()

class Session(pybuzz.session_subscriber):
    def __init__(self, **params):
        super().__init__()
        self.pid = params['pid']
        self.server_addr = params['server_addr']
        self.db_conn_str = params['db_conn_str']
        self.db_name = params['dt_src_name']

    def initialize(self):
        self.ds = pybuzz.create_bson_data_source(self.db_conn_str, self.db_name)
        self.session = pybuzz.join_simco_session(self.pid, pybuzz.create_bson_serializer(self.ds))

        self.session.initialize()

        #self.init(self.session)

        self.session.is_publisher(pybuzz.rudder_tag(), pybuzz.rudder_tag.SMH_DEMANDED_ANGLE)
        self.session.is_publisher(pybuzz.thruster_tag(), pybuzz.thruster_tag.SMH_DEMANDED_ROTATION |
                                                         pybuzz.thruster_tag.SMH_DEMANDED_POD |
                                                         pybuzz.thruster_tag.SMH_DEMANDED_ANGLE)
        #self.session.is_subscriber(pybuzz.vessel_tag(), pybuzz.vessel_tag.SMH_LINEAR_POSITION |
        #                                                pybuzz.vessel_tag.SMH_ANGULAR_POSITION |
        #                                                pybuzz.vessel_tag.SMH_LINEAR_VELOCITY |
        #                                                pybuzz.vessel_tag.SMH_ANGULAR_VELOCITY)

        self.session.connect(self.server_addr)

        ready.wait()


        if self.session.is_connected and \
           self.session.state == pybuzz.RUNNING:
            v = self.session.vessels[0]
            v.linear_position

            rd = v.rudders[0]
            rd.dem_angle = 2

            thr = v.thrusters[0]
            thr.dem_rotation=100

            self.session.sync(rd)
            self.session.sync(thr)


    def terminate(self):
        super().terminate(self.session)
        self.session.terminate()

    def on_element_added(self, instance):
        if instance.class_name == 'vessel':
            obj = pybuzz.typecast_as_vessel(instance)
            print(obj)
            #write initialization code in here
            rudders = obj.rudders
            thrusters = obj.thrusters

    def on_element_updated(self, updated):
        if updated.class_name == 'vessel':
            obj = pybuzz.typecast_as_vessel(updated)
            #write update code in here

            #obj.linear_position
            #obj.angular_position
            #obj.linear_velocity
            #obj.angular_velocity

    def on_element_removed(self, instance):
        if instance.class_name == 'vessel':
            pass
            #write termination code in here

    def on_network_connection_changed(self, connected):
        #write code to deal with events of network connection/disconnection
        if connected:
            print('Connecterd to server!')
        else:
            print('Disconnected from server!')

    def on_time_advanced(self, time):
        #write code triggered by changes in simulation step
        print(self.session.time)
        print(self.session.time_step)

    def on_error_reported(self, error_msg):
        print("Error: " + error_msg)

    def on_state_changed(self, state):
        # write code to run when the simulation starts
        if state == pybuzz.RUNNING:
            print('Simulation is running!')
            ready.set()


if __name__ == "__main__":
    try:
        args = {
            'pid': '0',
            'server_addr': '127.0.0.1',
            'db_conn_str': 'mongodb://10.1.1.176:27017',
            'dt_src_name': 'smh'
        }

        pybuzz.initialize_simco()

        sim = Session(**args)

        sim.initialize()

        k = ''
        while k != 's':
            k = input("Press s to stop")

        sim.terminate()
    except:
        for e in sys.exc_info():
            print(e)
    finally:
        if 'sim' in locals() and sim:
            sim.terminate()

        pybuzz.terminate_simco()
