#!/usr/bin/env python3

import os
import sys
import re

import getopt

import yaml
from yaml.loader import SafeLoader

#from signal import signal, SIGPIPE, SIG_DFL  
#signal(SIGPIPE,SIG_DFL)

def usage():
    print("Usage : {0} [-o output.yml] [input.xml]".format(sys.argv[0]))

def read_yaml(filepath):
    fp = open(filepath, mode="r", encoding="utf-8")
    data = yaml.load(fp, Loader=SafeLoader)
    fp.close()

    return data

def main():
    ret = 0

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hvo:",
            [
                "help",
                "version",
                "output=",
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

    for filepath in args:
        data = read_yaml(filepath)
        
    fp.write(
        yaml.dump(
            data,
            indent=2,
            sort_keys=True,
        )
    )
    fp.write('\n')

    if output is not None :
        fp.close()
    
if __name__ == "__main__":
    main()

