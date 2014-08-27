#! /usr/bin/env python

#  hdmi_ddc.py - HDMI DDC (I2C) definitions
# 
#  Adam Laurie <adam@aperturelabs.com>
#  http://www.aperturelabs.com
# 
#  This code is copyright (c) Aperture Labs Ltd., 2013, All rights reserved.

import sys
import os

# import hdcp-genkey for HDCP decoding
try:
        from generate_key import read_key_file, gen_sink_key, gen_source_key, output_human_readable
except:
        print
        print '  hdcp-genkey not found!'
        print
        print '  please fetch it from https://github.com/rjw57/hdcp-genkey and place generate_key.py'
        print '  in the same directory as', sys.argv[0]
        print
        exit(True)

try:
        master= open(os.path.dirname(sys.argv[0]) + '/hdcp-master.txt','r')
except:
        try:
                master= open(os.path.dirname(sys.argv[0]) + '/master-key.txt','r')
        except:
                print
                print '  no HDCP master key found!'
                print
                print '  please find a copy of hdcp-master.txt (or master-key.txt from hdcp-genkey) and'
                print '  place it in the same directory as', sys.argv[0]
                print
                exit(True)

# initialise the master key
global key_matrix
key_matrix = read_key_file(master)


# devices have two entries for convenience as I2C sets lower bit to signal READ/WRITE (1 == READ)
DDC_ADDRESS= 	{
		0x12:'Smart Battery Charger',
		0x13:'Smart Battery Charger',
		0x14:'Smart Battery Selector',
		0x15:'Smart Battery Selector',
		0x16:'Smart Battery',
		0x17:'Smart Battery',
		0x40:'PAL / NTSC Decoder',
		0x41:'PAL / NTSC Decoder',
		0x50:'DDC/CI Host Device',
		0x51:'DDC/CI Host Device',
		0x6E:'DDC/CI Display Device',
		0x6F:'DDC/CI Display Device',
		0x74:'Primary Link HDCP Port',
		0x75:'Primary Link HDCP Port',
		0x76:'Secondary Link HDCP Port',
		0x77:'Secondary Link HDCP Port',
		0x80:'Audio Processor',
		0x81:'Audio Processor',
		0xA0:'DDC2B Monitor (memory)',
		0xA1:'DDC2B Monitor (memory)',
		0xF0:'Pointer',
		0xF1:'Pointer',
		0xF2:'Audio Device',
		0xF3:'Audio Device',
		0xF4:'Serial Communication',
		0xF5:'Serial Communication',
		0xF6:'Calibration Device',
		0xF7:'Calibration Device',
		0xF8:'Input Device',
		0xF9:'Input Device',
		0xFA:'Reserved',
		0xFB:'Reserved',
		0xFC:'Reserved',
		0xFD:'Reserved',
		0xFE:'Reserved',
		0xFF:'Reserved',
		}

HDCP_OFFSET= 	{
		0x00:'Bksv (HDCP Receiver KSV)',
		0x05:'Rsvd',
		0x08:"Ri' (Link verification response)",
		0x0A:"Pj' (Enhanced Link Verification Response)",
		0x0B:'Rsvd',
		0x10:'Aksv (HDCP Transmitter KSV)',
		0x15:'Ainfo (ENABLE_1.1_FEATURES)',
		0x16:'Rsvd',
		0x18:'An (Session random number)',
		0x20:"V'.H0 (H0 part of SHA-1 hash value)",
		0x24:"V'.H1 (H1 part of SHA-1 hash value)",
		0x28:"V'.H2 (H2 part of SHA-1 hash value)",
		0x2C:"V'.H3 (H3 part of SHA-1 hash value)",
		0x30:"V'.H4 (H4 part of SHA-1 hash value)",
		0x34:'Rsvd',
		0x40:'Bcaps (Capabilities)',
		0x41:'Bstatus',
		0x43:'KSV FIFO (Key selection vector FIFO)',
		0x44:'Rsvd',
		0xC0:'Dbg (Implementation-specific debug registers)',
		}

# Bus Pirate I2C notation
I2C_START= 	'['
I2C_STOP= 	']'
I2C_ACK=	'+'
I2C_NAK=	'-'

# convert 8 bit int to human readable binary
def to_bin(x):
	return ''.join(x & (1 << i) and '1' or '0' for i in range(7,-1,-1))

# test data integrity and strip ACK/NAK
def i2c_clean(data):
	out= ''
	p= 0
	needack= False
	# we must start with a START
	if data[p] != I2C_START:
		return False
	out= I2C_START
	p += 1
	# now each hex byte should be ACK/NAK seperated, until STOP
	while p < len(data):
		# re-STARTs are also allowed
		if data[p] == I2C_START:
			p += 1
			out += I2C_START
			continue
		# check for ACK/NAK if flagged
		if needack:
			if data[p] != I2C_ACK and data[p] != I2C_NAK:
				return False
			needack= False
			p += 1
			continue
		if data[p] == I2C_STOP:
			if out:
				return out
			return False
		# next 4 bytes should be HEX data 0x--
		try:
			if data[p:p+2] != '0x':
				return False
			out += data[p+2:p+4]
			p += 4
			needack= True
		except:
			return False
	return False

# at some point this should be extended to decode the EDID data itself
def edid_decode(data, indent):
	print indent, 'EDID:',
	if not data[:3] == I2C_START + 'A1':
		print 'Failed! Invalid READ address:', data
	print data[3:]

# look for interesting bits of HDCP
def hdcp_decode(data, offset, indent):
	print indent, 'Offset:', 
	try:
		print HDCP_OFFSET[offset]
	except:
		print 'unknown! %02x' % offset
	indent += '  '
	# Ri'?
	if offset == 0x08:
		print indent, 'RI:',
		if not data[:3] == I2C_START + '75':
			print 'Invalid reply:', data
		else:
			print data[3:]
		return
	# KSV?
	if offset == 0x00 or offset == 0x10:
		# is this a response to a read request?
		if data[0] == I2C_START:
			data= data[3:]
		# convert to printable binary so we can check it's valid
		ksv= ''
		for x in range(0, len(data) / 2):
			ksv += to_bin(int(data[x * 2:x * 2 + 2], 16))
		# valid KSV has 20 * '1' and 20 * '0'
		if ksv.count('1') == 20 and ksv.count('0') == 20:
			# convert to a real number
			ksv= int(ksv,2)
			indent += '  '
			print indent, 'KSV:', '%010X' % ksv
			print
			if offset == 0x10:
				source_key= gen_source_key(ksv, key_matrix)
				output_human_readable(ksv, source_key, False)
			else:
				sink_key= gen_sink_key(ksv, key_matrix)
				output_human_readable(ksv, sink_key, True)
		else:
			print indent, '%010X' % int(ksv,2), '(INVALID)'
		return
	print indent, 'Payload:', data

# main wrapper - decide what protocol we're looking at
def ddc_decode(data, indent):
	# check & strip I2C ACK/NAK etc
	data= i2c_clean(data)
	if not data:
		return
	p= 0
	started= False
	identified= False
	address= None
	while(42):
		# start / restart
		if data[p] == I2C_START:
			identified= False
			if started:
				print '(restart)'
				indent += '  '
			started= True
			p += 1
			continue
		# stop
		if data[p] == I2C_STOP:
			print
			return
		# valid packet
		if started and not identified:
			identified= True
			address= int(data[p:p+2],16)
			print indent, 'Address: %s (%s)' % (data[p:p+2], DDC_ADDRESS[address]),
			if address & 0x01:
				print '(read)'
			else:
				print '(write)'
			p += 2
			try:
				offset= int(data[p:p+2],16)
				p += 2
				indent += '  '
			except:
				offset= None
		# HDCP?
		if address >= 0x74 and address <= 0x77:
			if not offset == None:
				hdcp_decode(data[p:], offset, indent)
			return
		# EDID?
		if address == 0xA0:
			if offset == 0x00:
				edid_decode(data[p:], indent)
			else:
				print indent, 'Invalid EDID offset!'
			return
		print indent, 'Payload:', data[p:]
		return
