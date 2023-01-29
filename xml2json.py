#!/usr/bin/env python3

import os
import sys
import re

import getopt

import json
import xmltodict

from datetime import datetime
import dateutil.parser

from pprint import pprint

def usage():
	print("Usage : {0} [-o output.jsonl] [input.xml]".format(sys.argv[0]))

def xml2json(fp, index, filepath) :
	fp_in = open(filepath, mode='r', encoding='utf-8')
	data = xmltodict.parse(fp_in.read())


	fp.write(
		json.dumps(
			data,
			indent=4,
			ensure_ascii=False,
		)
	)
	fp.write('\n')
	fp_in.close()

def main():
	ret = 0

	try:
		opts, args = getopt.getopt(
			sys.argv[1:],
			"hvi:o:d",
			[
				"help",
				"version",
				"index=",
				"output="
				"debug",
			]
		)
	except getopt.GetoptError as err:
		print(str(err))
		sys.exit(2)
	
	output = None
	index = None
	debug = 0
	
	for o, a in opts:
		if o == "-v":
			usage()
			sys.exit(0)
		elif o in ("-h", "--help"):
			usage()
			sys.exit(0)
		elif o in ("-i", "--index") :
			index = a
		elif o in ("-o", "--output"):
			output = a
		elif o in ("-d", "--debug"):
			debug = 1
		else:
			assert False, "unknown option"
	
	#if index is None :
	#	print('ERROR : no index option')
	#	ret += 1

	if ret != 0:
		sys.exit(1)

	if len(args) == 0 :
		usage()
		sys.exit(1)
	
	if output is not None :
		fp = open(output, mode='w', encoding='utf-8')
	else :
		fp = sys.stdout

	for filepath in args:
		xml2json(fp, index, filepath)
	
	if output is not None :
		fp.close()
	
if __name__ == "__main__":
	main()

