#!/usr/bin/env python3

"""
This is a NodeServer for Sense Monitoring written by automationgeek (Jean-Francois Tremblay) 
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com.
Using this Exploratory Work done from extracting Sense Monitoring Data using Python Library by scottbonline https://github.com/scottbonline/sense
"""

import polyinterface
import time
import json
from sense_energy import Senseable

LOGGER = polyinterface.LOGGER

with open('server.json') as data:
    SERVERDATA = json.load(data)
try:
    VERSION = SERVERDATA['credits'][0]['version']
except (KeyError, ValueError):
    LOGGER.info('Version not found in server.json.')
    VERSION = '0.0.0'

class Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Sense'
        self.initialized = False
        self.tries = 0
        self.email = None
        self.password = None
        self.sense = None
        
    def start(self):
        LOGGER.info('Started Sense NodeServer version %s', str(VERSION))
        try:
            
            self.setDriver('ST', 0)
            if 'email' in self.polyConfig['customParams'] and self.email is None:
                self.email = self.polyConfig['customParams']['email']
                LOGGER.info('Custom Email address specified: {}'.format(self.email))
            else:
                LOGGER.error('Please provide email address in custom parameters')
                return False
            
            if 'password' in self.polyConfig['customParams'] and self.password is None:
                self.password = self.polyConfig['customParams']['password']
                LOGGER.info('Password specified')
            else:
                LOGGER.error('Please provide password in custom parameters')
                return False
            
            self.sense =  Senseable(self.email,self.password)
            
            self.setDriver('ST', 1)
            self.setDriver('CPW', int(self.sense.active_power))
            self.discover()
                                                            
        except Exception as ex:
            LOGGER.error('Error starting Sense NodeServer: %s', str(ex))
            return False

    def shortPoll(self):
        self.setDriver('CPW', int(self.sense.active_power))

    def longPoll(self):
        self.query()

    def query(self):
        # self.reportDrivers()
        for node in self.nodes:
            if self.nodes[node].address != self.address and self.nodes[node].do_poll:
                self.nodes[node].query()
        
    def discover(self, *args, **kwargs):
        time.sleep(1)
        
        for device in  self.sense.get_discovered_device_data():
            if device is not None: 
                if device['tags']['Revoked'] == 'false': 
                    self.addNode(SenseDetectedDevice(self, self.address, device['id'], device['name'])) 
    
    def delete(self):
        LOGGER.info('Deleting Sense')
        
    id = 'controller'
    commands = {}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2},
               {'driver': 'CPW', 'value': 0, 'uom': 73}]
    
class SenseDetectedDevice(polyinterface.Node):

    def __init__(self, controller, primary, address, name):
        super(SenseDetectedDevice, self).__init__(controller, primary, address, name)
        self.do_poll = True
        self.timeout = 5.0
        self.query()
        
    def start(self):
        pass                                     
    
    def query(self):
        self.updateDevice()
        self.reportDrivers()

    def updateDevice(self):
        self.setDriver('ST', 0)
        for x in self.parent.sense.active_devices:
            if x == self.name:
                self.setDriver('ST', 100)
        
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'CPW', 'value': 0, 'uom': 73}]
    
    id = 'SENSEDEVICE'
    commands = {
                    'QUERY': query          
                }
    
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('SenseNodeServer')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
