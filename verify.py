#!/usr/bin/env python3

import os
import sys
import re

import getopt
import json

from datetime import datetime

from lxml import etree
from io import StringIO, BytesIO

from pprint import pprint

#from signal import signal, SIGPIPE, SIG_DFL  
#signal(SIGPIPE,SIG_DFL)

def usage():
    print("Usage : {0} [-o output.json] [input.xml]".format(sys.argv[0]))

def main():
    ret = 0

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hvo:",
            [
                "help",
                "version",
                "output="
            ]
        )
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    output = None
    
    for o, a in opts:
        if o == "-v":
            usage()
            sys.exit(0)
        elif o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--output"):
            output = a
        else:
            assert False, "unknown option"
    
    if ret != 0:
        sys.exit(1)

    if len(args) == 0 :
        usage()
        sys.exit(1)
    
    if output is not None :
        fp = open(output, mode='w', encoding='utf-8')
    else :
        fp = sys.stdout

    count = 0

    for filepath in args:
        fp_in = open(filepath, mode="r", encoding='utf-8')
        while True :
            line = fp_in.readline()
            if not line :
                break
            line = re.sub(r'\r?\n?$', '', line)
            m = re.search(r'<DEFINITION-REF ', line)
            if m :
                count += 1
        fp_in.close()

    fp.write("num of defref : {0}\n".format(count))

    if output is not None :
        fp.close()
    
if __name__ == "__main__":
    main()

