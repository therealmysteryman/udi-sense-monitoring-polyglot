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
        self.tries = 0
        self.email = None
        self.password = None
        self.sense = None
        self.discovery_thread = None
        
    def start(self):
        LOGGER.info('Started Sense NodeServer version %s', str(VERSION))
        try:
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
            
        except Exception as ex:
            LOGGER.error('Error starting Sense NodeServer: %s', str(ex))
            return False
        
        self.connectSense()
        self.query()
        self.discover()
        
    def shortPoll(self):
        for node in self.nodes:
            self.nodes[node].query()

    def longPoll(self):
        time.sleep(5)
        self.connectSense()
    
    def connectSense(self):
        try:
            self.sense =  Senseable(self.email,self.password)
        except Exception as ex:
            LOGGER.error('Unable to connect to Sense API: %s', str(ex))
    
    def query(self):
        try:
            self.setDriver('ST', 1, True)
            self.setDriver('CPW', int(self.sense.active_power), True)
            self.setDriver('GV6', int(self.sense.active_solar_power), True)
            self.setDriver('GV7', int(self.sense.daily_usage), True)
            self.setDriver('GV8', int(self.sense.daily_production), True)
            self.setDriver('GV9', int(self.sense.weekly_usage), True)
            self.setDriver('GV10', int(self.sense.weekly_production), True)
            self.setDriver('GV11', int(self.sense.monthly_usage), True)
            self.setDriver('GV12', int(self.sense.monthly_production), True)
            self.setDriver('GV13', int(self.sense.yearly_usage), True)
            self.setDriver('GV14', int(self.sense.yeary_production), True)
        except Exception as ex:
            LOGGER.error('query, unable to retrieve Sense Monitor usage: %s', str(ex))
    
    def discover(self, *args, **kwargs):    
        if self.discovery_thread is not None:
            if self.discovery_thread.isAlive():
                LOGGER.info('Discovery is still in progress')
                return
        self.discovery_thread = Thread(target=self._discovery_process)
        self.discovery_thread.start()
    
    def _discovery_process(self):
        time.sleep(1)
        try :
            for device in  self.sense.get_discovered_device_data():
                if device is not None: 
                    if device['tags']['Revoked'] == 'false':
                        self.addNode(SenseDetectedDevice(self, self.address, device['id'], device['name']))                     
        except Exception as ex:
            LOGGER.error('discover: %s', str(ex))
    
    def runDiscover()
        self.discover()
    
    def delete(self):
        LOGGER.info('Deleting Sense Node Server')
        
    id = 'controller'
    commands = {
                    'QUERY': query,
                    'DISCOVERY' : runDiscover
                }
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
        super(SenseDetectedDevice, self).__init__(controller, primary, address.lower(), name)
        self.nameOrig = name
        self.addressOrig = address
        self.timeout = 5.0
          
    def start(self):
        self.query()                                   
        
    def query(self):
        try :
            # Device Power Status
            self.setDriver('ST', 0,True)
            for x in self.parent.sense.active_devices:
                if x == self.nameOrig:
                    self.setDriver('ST', 100, True)

            # Device Info
            deviceInfo = self.parent.sense.get_device_info(self.addressOrig)
            if deviceInfo is not None:
                    if 'usage' in deviceInfo : 
                        self.setDriver('GV1', int(deviceInfo['usage']['avg_monthly_runs']),True)
                        self.setDriver('GV5', int(deviceInfo['usage']['avg_watts']),True)
                        self.setDriver('GV2', int(deviceInfo['usage']['avg_monthly_KWH']),True)
                        self.setDriver('GV3', int(deviceInfo['usage']['current_month_runs']),True)
                        self.setDriver('GV4', int(deviceInfo['usage']['current_month_KWH']),True)
                        
        except Exception as ex:
            LOGGER.error('updateDevice: %s', str(ex))

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
