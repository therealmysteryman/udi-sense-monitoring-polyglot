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
            self.query()
            self.discover()
                                                            
        except Exception as ex:
            LOGGER.error('Error starting Sense NodeServer: %s', str(ex))
            return False

    def shortPoll(self):
        self.query()

    def longPoll(self):
        try:
            # Force a reconnect need to find a better solutions
            self.sense =  Senseable(self.email,self.password)
        except Exception as ex:
            LOGGER.error('Unable to connect to Sense API: %s', str(ex))
        self.discover()
        
    def query(self):
        try:
            self.setDriver('ST', 1)
            self.setDriver('CPW', int(self.sense.active_power))
            self.setDriver('GV6', int(self.sense.active_solar_power))
            self.setDriver('GV7', int(self.sense.daily_usage))
            self.setDriver('GV8', int(self.sense.daily_production))
            self.setDriver('GV9', int(self.sense.weekly_usage))
            self.setDriver('GV10', int(self.sense.weekly_production))
            self.setDriver('GV11', int(self.sense.monthly_usage))
            self.setDriver('GV12', int(self.sense.monthly_production))
            self.setDriver('GV13', int(self.sense.yearly_usage))
            self.setDriver('GV14', int(self.sense.yeary_production))
        except Exception as ex:
            LOGGER.error('Unable to retrieve usage: %s', str(ex))
        
        # self.reportDrivers()
        for node in self.nodes:
            if self.nodes[node].address != self.address and self.nodes[node].do_poll:
                self.nodes[node].query()
        
    def discover(self, *args, **kwargs):
        time.sleep(1)
        for device in  self.sense.get_discovered_device_data():
            if device is not None: 
                if 'Revoked' in device and device['tags']['Revoked'] == 'false':
                    if 'id' in device and 'name' in device:
                        self.addNode(SenseDetectedDevice(self, self.address, device['id'], device['name'])) 
    
    def delete(self):
        self.sense = None
        LOGGER.info('Deleting Sense Node Server')
        
    id = 'controller'
    commands = {}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2},
               {'driver': 'CPW', 'value': 0, 'uom': 73},
               {'driver': 'GV6', 'value': 0, 'uom': 73},
               {'driver': 'GV7', 'value': 0, 'uom': 73},
               {'driver': 'GV8', 'value': 0, 'uom': 73},
               {'driver': 'GV9', 'value': 0, 'uom': 73},
               {'driver': 'GV10', 'value': 0, 'uom': 73},
               {'driver': 'GV11', 'value': 0, 'uom': 73},
               {'driver': 'GV12', 'value': 0, 'uom': 73},
               {'driver': 'GV13', 'value': 0, 'uom': 73},
               {'driver': 'GV14', 'value': 0, 'uom': 73}]
    
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
        # self.reportDrivers()

    def updateDevice(self):
        # Device Power Status
        self.setDriver('ST', 0)
        for x in self.parent.sense.active_devices:
            if x == self.name:
                self.setDriver('ST', 100)
        
        # Device Info
        deviceInfo = self.parent.sense.get_device_info(self.address)
        if deviceInfo is not None:
            if 'usage' in deviceInfo:
                if 'avg_monthly_runs' in deviceInfo:
                    self.setDriver('GV1', deviceInfo['usage']['avg_monthly_runs'])
                if 'avg_watts' in deviceInfo:
                    self.setDriver('GV5', int(deviceInfo['usage']['avg_watts']))
                if 'avg_monthly_KWH' in deviceInfo:
                    self.setDriver('GV2', int(deviceInfo['usage']['avg_monthly_KWH']))
                if 'current_month_runs' in deviceInfo:    
                    self.setDriver('GV3', deviceInfo['usage']['current_month_runs'])
                if 'current_month_KWH' in deviceInfo:    
                    self.setDriver('GV4', int(deviceInfo['usage']['current_month_KWH']))
        
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'GV5', 'value': 0, 'uom': 73}, 
               {'driver': 'GV1', 'value': 0, 'uom': 0}, 
               {'driver': 'GV2', 'value': 0, 'uom': 30}, 
               {'driver': 'GV3', 'value': 0, 'uom': 0}, 
               {'driver': 'GV4', 'value': 0, 'uom': 30} ]

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
