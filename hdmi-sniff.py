#! /usr/bin/env python

#  hdmi-sniff.py - sniff HDMI DDC (I2C) traffic with a GPHHT or Bus Pirate
# 
#  Adam Laurie <adam@aperturelabs.com>
#  http://www.aperturelabs.com
# 
#  This code is copyright (c) Aperture Labs Ltd., 2013, All rights reserved.
#
#  This code depends in part on https://github.com/rjw57/hdcp-genkey
#
#  You will need a Bus Pirate and an HDMI breakout cable
#
#     http://dangerousprototypes.com/docs/Bus_Pirate
#

import sys
import serial
import hdmi_ddc

if len(sys.argv) == 1:
	print
	print 'Usage: %s <SERIAL PORT>' % sys.argv[0]
	print
	exit(True)

port= sys.argv[1]
baud= 115200
timeout= 0.02
bp= serial.Serial(sys.argv[1], baud, timeout= timeout)
reader= 'bp'

# connect and configure Bus Pirate
# yes, I know this is ugly but it's a *really* quick hack!
print
print '  Connecting...'
bp.write('\n\n')
while bp.readline():
	continue
bp.write('i\n')
bp.readline()
response= bp.readline().strip()
if response.find('Bus Pirate') == 0:
	print '  Detected Bus Pirate'
else:
	print '  No Bus Pirate detected. Assuming GPHHT.'
	reader= 'gphht'
while bp.readline():
	continue
# configure for I2C sniffing
if reader == 'bp':
	# Bus Pirate
	bp.write('\nm\n')
	while bp.readline():
		continue
	# make sure we're in a known mode
	bp.write('\n')
	bp.readline()
	bp.readline()
	response= bp.readline().strip()
	if response != 'HiZ>':
		print "can't reset Bus Pirate! Try power cycling!"
		print 'response:', response
		exit(True)
	print '  Switching to I2C mode'
	bp.write('m\n')
	while bp.readline():
		continue
	bp.write('4\n\n')
	while response != 'Ready':
		response= bp.readline().strip()
	response= bp.readline().strip()
	if response != 'I2C>':
		print "can't switch to I2C! Try power cycling!"
		print 'response:', response
		exit(True)
	print '  Sniffing...'
	bp.write('(2)\n')
	bp.readline()
	bp.readline()
	response= bp.readline().strip()
	if response != 'Any key to exit':
		print "can't sniff!"
		print 'response:', response
		exit(True)
else:
	# GPHHT
	bp.write('\n')
	while bp.readline():
		continue
	bp.write('command\n')
	bp.read(1)
	bp.write('raw\n')
	bp.read(1)
	bp.write('hex\n')
	bp.read(1)
	bp.write('i2c\n')
	bp.read(1)
	print '  Sniffing...'
	bp.write('readl\n')
	bp.read(1)

# now do the actual sniffing
while 42:
	response= bp.readline().strip()
	if response:
		for ddc in response.split(hdmi_ddc.I2C_STOP):
			hdmi_ddc.ddc_decode(ddc + hdmi_ddc.I2C_STOP, '   ')
			print
