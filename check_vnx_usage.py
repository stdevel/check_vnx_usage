#!/usr/bin/env python
# -*- coding: utf-8 -*-

# check_vnx_usage.py - a script for checking a EMC² VNX
# filer's storage health
#
# 2016 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#

from optparse import OptionParser, OptionGroup
import os
import subprocess
import logging
import re
import sys

#setting logger and supported API levels
LOGGER =  logging.getLogger('check_vnx_usage')

#some script-wide variables
state=0
os.environ['NAS_DB'] = "/nas"

def check_filesystems(fs):
	global state
	
	#get file system usage
	raw_usage = run_cmd("/nas/bin/server_df ALL | grep ' /fs'")
	raw_usage = re.sub(' +',' ', raw_usage)
	raw_usage = raw_usage.split('\n')
	
	snip_fs = ""
	perfdata = " | "
	
	#check _all_ the relevant file systems
	for line in raw_usage:
		if line != "":
			#split fields
			values = line.split(' ')
			
			#match if relevant or all file systems
			if values[0] in options.fs_path or len(options.fs_path) == 0:
				#yep, commas can safe lifes
				#if snip_fs != "" and len(options.fs_path) > 1: snip_fs = snip_fs + ", "
				if snip_fs != "" : snip_fs = snip_fs + ", "
				
				#check usage
				usage = int(values[4].replace("%", ""))
				if usage >= options.crit_thres:
					#critical
					LOGGER.debug("File system '" + values[0] + "' consumption (" + values[3] + ") is more than critical threshold (" + str(usage) + ")")
					snip_fs = snip_fs + "file system '" + values[0] + "' CRITICAL (" + values[4] + ")"
					set_code(2)
				elif usage >= options.warn_thres:
					#warning
					LOGGER.debug("File system '" + values[0] + "' consumption (" + values[3] + ") is more than warning threshold (" + str(usage) + ")")
					snip_fs = snip_fs + "file system '" + values[0] + "' WARNING (" + values[4] + ")"
					set_code(1)
				else:
					#ok
					LOGGER.debug("File system '" + values[0] + "' consumption (" + values[3] + ") is okay")
					snip_fs = snip_fs + "file system '" + values[0] + "' OK (" + values[4] + ")"
				
				#set performance data
				if options.show_perfdata:
					LOGGER.debug("Filesystem '" + values[0] + "' - size: " + values[1] + " kbytes total, " + values[2] + " kbytes used, " + values[3] + " kbytes free")
					perfdata = perfdata + "'" + values[0] + "_size" + "'=" + values[1] + " '" + values[0] + "_used'=" + values[2] + " '" + values[0] + "_free'=" + values[3] + " "
	
	#return result and performance data
	print get_return_str() + ": " + snip_fs + perfdata
	sys.exit(int(state))



def set_code(int):
	#set result code
	global state
	if int > state: state = int



def get_return_str():
	#get return string
	if state == 3: return "UNKNOWN"
	elif state == 2: return "CRITICAL"
	elif state == 1: return "WARNING"
	else: return "OK"



def run_cmd(cmd=""):
	#run the command, it's tricky!
	output = subprocess.Popen("LANG=C " + cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
	LOGGER.debug("Output of '" + cmd + "' => '" + output.strip() + "'")
	return output



if __name__ == "__main__":
	#define description, version and load parser
	desc='''%prog is used to check a EMC² VNX filer's storage consumption.
	
	Checkout the GitHub page for updates: https://github.com/stdevel/check_vnx_usage'''
	parser = OptionParser(description=desc,version="%prog version 0.5.0")
	
	gen_opts = OptionGroup(parser, "Generic options")
	stor_opts = OptionGroup(parser, "Storage options")
	parser.add_option_group(gen_opts)
	parser.add_option_group(stor_opts)
	
	#-d / --debug
	gen_opts.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs")
	
	#-P / --show-perfdata
	gen_opts.add_option("-P", "--show-perfdata", dest="show_perfdata", default=False, action="store_true", help="enables performance data, requires -i (default: no)")
	
	#-p / --path
	stor_opts.add_option("-p", "--path", dest="fs_path", default=[], type="string", action="append", help="file system path")
	
	#-w / --warning
	stor_opts.add_option("-w", "--warning", dest="warn_thres", default=80, type=int, action="store", help="consumption warning threshold (default: 80%)")
	
	#-c / --critical
	stor_opts.add_option("-c", "--critical", dest="crit_thres", default=90, type=int, action="store", help="consumption critical threshold (default: 90%)")
	
	#parse arguments
	(options, args) = parser.parse_args()
	
	#set logging
	if options.debug:
		logging.basicConfig(level=logging.DEBUG)
		LOGGER.setLevel(logging.DEBUG)
	else:
		logging.basicConfig()
		LOGGER.setLevel(logging.INFO)
	
	#debug outputs
	LOGGER.debug("OPTIONS: " + str(options))
	
	#check filesystems
	check_filesystems(options.fs_path)
