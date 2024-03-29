#!/usr/bin/env python3

"""
This is a NodeServer for Sense Monitoring written by automationgeek (Jean-Francois Tremblay)  
based on the NodeServer template for Polyglot v2 written in Python2/3 by Einstein.42 (James Milne) milne.james@gmail.com.
Using this Exploratory Work done from extracting Sense Monitoring Data using Python Library by scottbonline https://github.com/scottbonline/sense
"""

import polyinterface
import time
import json
import sys
from copy import deepcopy
from threading import Thread
from sense_energy import Senseable

LOGGER = polyinterface.LOGGER
SERVERDATA = json.load(open('server.json'))
VERSION = SERVERDATA['credits'][0]['version']

def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    f.close()
    return { 'version': pv }
    
class Controller(polyinterface.Controller):

    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'Sense'
        self.email = None
        self.password = None
        self.sense = None
        self.discovery_thread = None
        self.hb = 0
        self.queryON = False
        
    def start(self):
        LOGGER.info('Started Sense NodeServer version %s', str(VERSION))
        try:
            if 'email' in self.polyConfig['customParams'] and self.email is None:
                self.email = self.polyConfig['customParams']['email']
            else:
                LOGGER.error('Please provide email address in custom parameters')
                return False
            
            if 'password' in self.polyConfig['customParams'] and self.password is None:
                self.password = self.polyConfig['customParams']['password']
            else:
                LOGGER.error('Please provide password in custom parameters')
                return False
            
            self.check_profile()
            self.heartbeat()
            self.connectSense()
            self.discover()
            
        except Exception as ex:
            LOGGER.error('Error starting Sense NodeServer: %s', str(ex))
            return False
        
    def shortPoll(self):
        try :
            if self.discovery_thread is not None:
                if self.discovery_thread.is_alive():
                    LOGGER.debug('Skipping shortPoll() while discovery in progress...')
                    return
                else:
                    self.discovery_thread = None
            self.update()
        except Exception as ex:
            LOGGER.error('Error shortPoll: %s', str(ex))
            
    def longPoll(self):
        try :
            if self.discovery_thread is not None:
                if self.discovery_thread.is_alive():
                    LOGGER.debug('Skipping longPoll() while discovery in progress...')
                    return
                else:
                    self.discovery_thread = None
            self.connectSense()
            self.heartbeat()
        except Exception as ex:
            LOGGER.error('Error longPoll: %s', str(ex))
        
    def query(self):
        for node in self.nodes:
            self.nodes[node].reportDrivers()
            
    def update(self) :       
        try:
            self.sense.update_realtime()
            self.sense.update_trend_data()
            
            self.setDriver('ST', 1)
            self.setDriver('CPW', int(self.sense.active_power) if self.sense.active_power != None else 0 )
            self.setDriver('GV6', int(self.sense.active_solar_power) if self.sense.active_solar_power != None else 0 ) 
            self.setDriver('GV7', int(self.sense.daily_usage) if self.sense.daily_usage != None else 0 )  
            self.setDriver('GV8', int(self.sense.daily_production) if self.sense.daily_production != None else 0 )
            self.setDriver('GV9', int(self.sense.weekly_usage) if self.sense.weekly_usage != None else 0 )
            self.setDriver('GV10', int(self.sense.weekly_production) if self.sense.weekly_production != None else 0 )
            self.setDriver('GV11', int(self.sense.monthly_usage) if self.sense.monthly_usage != None else 0 )
            self.setDriver('GV12', int(self.sense.monthly_production) if self.sense.monthly_production != None else 0 )
            self.setDriver('GV13', int(self.sense.yearly_usage) if self.sense.yearly_usage != None else 0 )  
        except Exception as ex:
            LOGGER.error('query, unable to retrieve Sense Monitor usage: %s', str(ex))
        
        for node in self.nodes:
            if  self.nodes[node].queryON == True :
                self.nodes[node].update()

    def heartbeat(self):
        self.l_info('heartbeat','hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0
    
    def l_info(self, name, string):
        LOGGER.info("%s:%s: %s" %  (self.id,name,string))
    
    def connectSense(self):
        try:
            self.sense = Senseable()
            self.sense.authenticate(self.email,self.password)   
        except Exception as ex:
            LOGGER.error('Unable to connect to Sense API: %s', str(ex))
    
    def discover(self, *args, **kwargs):    
        if self.discovery_thread is not None:
            if self.discovery_thread.is_alive():
                LOGGER.info('Discovery is still in progress')
                return
        self.discovery_thread = Thread(target=self._discovery_process)
        self.discovery_thread.start()
    
    def _discovery_process(self):
        for device in self.sense.get_discovered_device_data():
            if device is not None: 
                try :
                    if device["tags"]["DeviceListAllowed"] == "true" and device['name'] != "Always On" and device['name'] != "Unknown" :
                        self.addNode(SenseDetectedDevice(self, self.address, device['id'], device['name']))                    
                except Exception as ex: 
                    LOGGER.error('discover device name: %s', str(device['name']))
    
    def runDiscover(self,command):
        self.discover()
    
    def check_profile(self):
        self.profile_info = get_profile_info(LOGGER)
        # Set Default profile version if not Found
        cdata = deepcopy(self.polyConfig['customData'])
        LOGGER.info('check_profile: profile_info={0} customData={1}'.format(self.profile_info,cdata))
        if not 'profile_info' in cdata:
            cdata['profile_info'] = { 'version': 0 }
        if self.profile_info['version'] == cdata['profile_info']['version']:
            self.update_profile = False
        else:
            self.update_profile = True
            self.poly.installprofile()
        LOGGER.info('check_profile: update_profile={}'.format(self.update_profile))
        cdata['profile_info'] = self.profile_info
        self.saveCustomData(cdata)
    
    def install_profile(self,command):
        LOGGER.info("install_profile:")
        self.poly.installprofile()
    
    def delete(self):
        LOGGER.info('Deleting Sense Node Server')
        
    id = 'controller'
    commands = {
                    'QUERY': query,
                    'DISCOVERY' : runDiscover
                }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2},
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
        newaddr = address.lower().replace('dcm','').replace('-','')
        super(SenseDetectedDevice, self).__init__(controller, primary,newaddr, name)
        self.queryON = True
        self.nameOrig = name
        self.addressOrig = address
        
        self.setDriver('GV1', 0)
        self.setDriver('GV2', 0)
        self.setDriver('GV3', 0)
        self.setDriver('GV4', 0)
        self.setDriver('GV5', 0)
          
    def start(self):
        pass
  
    def query(self):
        self.reportDrivers()

    def update(self):
        try :
            # Device Power Status
            val = 0
            for x in self.parent.sense.active_devices:
                if x == self.nameOrig:
                    val = 100
                    break
            self.setDriver('ST',val)
                    
            # Device Info
            deviceInfo = self.parent.sense.get_device_info(self.addressOrig)
            if deviceInfo is not None:
                    if 'usage' in deviceInfo : 
                        self.setDriver('GV1', int(deviceInfo['usage']['avg_monthly_runs']))
                        self.setDriver('GV5', int(deviceInfo['usage']['avg_watts']))
                        self.setDriver('GV2', int(deviceInfo['usage']['avg_monthly_KWH']))
                        self.setDriver('GV3', int(deviceInfo['usage']['current_month_runs']))
                        self.setDriver('GV4', int(deviceInfo['usage']['current_month_KWH']))
        except Exception as ex:
            LOGGER.error('updateDevice: %s', str(ex))
            
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 78},
               {'driver': 'GV5', 'value': 0, 'uom': 73}, 
               {'driver': 'GV1', 'value': 0, 'uom': 25}, 
               {'driver': 'GV2', 'value': 0, 'uom': 30}, 
               {'driver': 'GV3', 'value': 0, 'uom': 25}, 
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
