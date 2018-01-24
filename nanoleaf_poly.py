#!/usr/bin/env python3

"""
This is a NodeServer for Sense Monitoring written by automationgeek (Jean-Francois Tremblay) 
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com.
Using this Exploratory Work done from extracting Sense Monitoring Data using Python Library by scottbonline https://github.com/scottbonline/sense
"""

import polyinterface
import time
import json

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
        self.requestNewToken = 0
        
    def start(self):
        LOGGER.info('Started Sense NodeServer version %s', str(VERSION))
        try:
            self.setDriver('ST', 1)
                                                            
        except Exception as ex:
            LOGGER.error('Error starting Sense NodeServer: %s', str(ex))
            self.setDriver('ST', 0)
            return False

    def shortPoll(self):
        pass

    def longPoll(self):
        self.query()

    def query(self):
        # self.reportDrivers()
        for node in self.nodes:
            if self.nodes[node].address != self.address and self.nodes[node].do_poll:
                self.nodes[node].query()
        
    def discover(self, *args, **kwargs):
        time.sleep(1)
        self.addNode(SenseDetectedDevice(self, self.address, 'myaurora', 'MyAurora'))

    def delete(self):
        LOGGER.info('Deleting Sense')
        
    id = 'controller'
    commands = {}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    
class SenseDetectedDevice(polyinterface.Node):

    def __init__(self, controller, primary, address, name):
        super(AuroraNode, self).__init__(controller, primary, address, name)
        self.do_poll = True
        self.timeout = 5.0
        
        self.my_aurora = SenseDetectedDevice(self.parent.nano_ip,self.parent.nano_token)
        self.query()

    def start(self):
        pass                                     
    
    def query(self):
        self.reportDrivers()

    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'GV3', 'value': 0, 'uom': 51},
               {'driver': 'GV4', 'value': 1, 'uom': 25}]
    
    id = 'SENSE_DEVICE'
    commands = {
                    'QUERY': query          
                }
    
if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('SenseMonitoringNodeServer')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
