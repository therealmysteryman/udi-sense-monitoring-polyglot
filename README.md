
## This nodeserver has been converted to run on PG3. The code has been moved to https://github.com/UniversalDevicesInc-PG3/udi-sense-monitoring-polyglot

# Sense Monitoring Polyglot V2 Node Server

![Build Status](https://travis-ci.org/therealmysteryman/udi-sense-monitoring-polyglot.svg?branch=master)

This Poly provides an interface between Sense Monitoring using undocumented API and Polyglot v2 server. Provide Electricity Usage and Status of a Device. This use undocumented API from Sense via a Python Library (https://github.com/scottbonline/sense).

#### Installation

Installation instructions
You can install it manually running

1. cd ~/.polyglot/nodeservers
2. git clone https://github.com/therealmysteryman/udi-sense-monitoring-polyglot.git
3. run ./install.sh to install the required dependency.
3. Create a customs variables email -> email_address_of_sense_account, 
                              password -> password_of_sense_account

#### Usage

This will create one node for the controller with the Sense Power Usage and then one node for each detected device with their current power usage and their status (on / off). Those value a refreshed every 60 seconds.

#### Known Issues

1. If a device is removed from Sense, it won't be removed from the node server you need to manually delete it.
2. If you rename or merge a device, you may need to delete the old device in the node server and re-import it.

#### Source

1. Based on the Node Server Template - https://github.com/Einstein42/udi-poly-template-python
2. Library for accessing the Sense API - https://github.com/scottbonline/sense
