#!/usr/bin/env python3

import os
import sys
import re

import getopt
import json
import yaml

from datetime import datetime

import sqlite3

from lxml import etree

from pprint import pprint

#from signal import signal, SIGPIPE, SIG_DFL  
#signal(SIGPIPE,SIG_DFL)

def usage():
    print("Usage : {0} [-o output.json] [input.xml]".format(sys.argv[0]))

def xpath2dict(data, path, val) :
    debug = 0
    if re.search(r'/AppMode1$', path) :
        debug = 1
        print("DEBUG found {0}".format(path))
        print("DEBUG val is {0}".format(val))

    tokens = re.split(r'/', path)

    if debug :
        print('tokens is {0}'.format(tokens))

    cur = data
    for i in range(len(tokens) - 1) :
        token = tokens[i]
        if token == '' :
            continue
        
        if not token in cur :
            cur[token] = {}
        
        cur = cur[token]

    i += 1
    token = tokens[i]

    if debug :
        print("data is {0}".format(data))
        print("cur is {0}".format(cur))
        print("token is {0}".format(token))

    if val is None :
        cur[token] = {}
        pass
    else :
        if val == 'true' :
            val = True
        elif val == 'talse' :
            val = False
        elif val.isdecimal() :
            val = int(val)

        if not token in cur:
            cur[token] = val
        elif type(cur[token]) is list :
            cur[token].append(val)
        else :
            tmp = cur[token]
            cur[token] = [ tmp, val]
    
def get_text(node, nss, tag) :
    text = None
    item = node.find("./ns:{0}".format(tag), nss)
    if item is not None:
        text = item.text
    return text

def get_parameter_values(indent, parent, userdata, container) :
    params = None
    name2defref = {}

    nss = userdata["nss"]
    package = userdata["package"]
    module  = userdata["module"]

    items = parent.findall("./*/*/ns:DEFINITION-REF/..", nss)
    if items is None :
        return params

    for item in items :
        defref = get_text(item, nss, "DEFINITION-REF")
        value = get_text(item, nss, "VALUE")
        valref = get_text(item, nss, "VALUE-REF")

        if value is not None:
            pass
        elif valref is not None :
            value = valref
        else :
            value = ''

        name = re.sub(r'.+/', '', defref)
        
        if value != "" :
            #pprint(name)
            #pprint(params)
            #print("DEBUG : value is {0}".format(value))
            if params is None :
                params = {}

            if not name in params :
                params[name] = value
            elif type(params[name]) is list :
                params[name].append(value)
            else :
                tmp = params[name]
                params[name] = [ tmp, value ]
            
            name2defref[name] = defref

    return params, name2defref

def parse_container(indent, parent, userdata, path) :
    fp = userdata["fp"]
    nss = userdata["nss"]
    data = userdata["data"]
    show_definition_ref = userdata['show_definition_ref']

    sname   = get_text(parent, nss, "SHORT-NAME")
    defref = get_text(parent, nss, "DEFINITION-REF")


    if not userdata['long_definition_ref'] :
        defref = re.sub(r'.+/', '', defref)

    container = path + "/" + sname

    xpath2dict(data, container, None)
    if show_definition_ref :
        xpath2dict(data, container + "/DefinitionRef", defref)

    params, name2defref = get_parameter_values(indent + "  ", parent, userdata, container)
    if params is not None :
        for name in params :
            vals = []
            if type(params[name]) is list :
                vals = params[name]
            else :
                vals = [ params[name] ]
            for val in vals :
                if not show_definition_ref :
                    xpath2dict(data, container + "/" + name, val)
                else :
                    xpath2dict(data, container + "/" + name, None)
                    xpath2dict(data, container + "/" + name + "/DefinitionRef", name2defref[name])
                    xpath2dict(data, container + "/" + name + "/Value", val)
                userdata['count'] += 1

    nodes = parent.findall("./ns:SUB-CONTAINERS/ns:ECUC-CONTAINER-VALUE", nss)
    for node in nodes :
        parse_container(indent + "  ", node, userdata, container)
        userdata['count'] += 1

def parse_module(indent, parent, userdata, path) :
    fp = userdata["fp"]
    nss = userdata["nss"]
    data = userdata["data"]

    nodes = parent.findall(".//ns:ECUC-MODULE-CONFIGURATION-VALUES", nss)
    for node in nodes :
        name = get_text(node, nss, "SHORT-NAME")

        newpath = path + "/" + name

        type_name = get_text(node, nss, "DEFINITION-REF")

        userdata["module"] = name
        userdata['count'] += 1
        xpath2dict(data, newpath, None)

        cons = node.findall(".//ns:CONTAINERS/ns:ECUC-CONTAINER-VALUE", nss)
        for con in cons :
            userdata['count'] += 1
            parse_container(indent + "  ", con, userdata, newpath)

def parse_package(indent, parent, userdata, path) :
    nss = userdata["nss"]
    fp = userdata["fp"]

    data = userdata["data"]

    nodes = parent.findall(".//ns:AR-PACKAGE", nss)
    for node in nodes :
        name = get_text(node, nss, "SHORT-NAME")
        newpath = path + "/" + name
        userdata["package"] = name
        xpath2dict(data, newpath, None)

        parse_module(indent + "  ", node, userdata, newpath)

def main():
    ret = 0

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hvo:l",
            [
                "help",
                "version",
                "output=",
                "long-definition-ref"
            ]
        )
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    output = None
    long_definition_ref = False
    show_definition_ref = False
    
    for o, a in opts:
        if o == "-v":
            usage()
            sys.exit(0)
        elif o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--output"):
            output = a
        elif o in ("-l", "--long-definition-ref"):
            long_definition_ref = True
        elif o in ("-s", "--show-definition-ref"):
            show_definition_ref = True
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

    indent = ""
    userdata = {
        "count" : 0,
        "package" : "",
        "module"  : "",
        "nss" : None,
        "fp"  : fp,
        "data" : {},
        "long_definition_ref" : long_definition_ref,
        "show_definition_ref" : show_definition_ref,
    }
    path = ""
    for filepath in args:
        tree = etree.parse(filepath)
        root = tree.getroot()
        m = re.search(r'\{(.+)\}', root.tag)
        if m :
            ns = m.group(1)
        else :
            print('ERROR : can not get namespace')
            sys.exit(1)

        userdata["nss"] = {
            "ns" : ns,
        }

        parse_package(indent, root, userdata, path)
    
    print("count is {0}".format(userdata['count']))

    fp.write(
        yaml.dump(
            userdata['data'],
            indent=2,
            sort_keys=True,
        )
    )
    fp.write('\n')

    if output is not None :
        fp.close()
    
if __name__ == "__main__":
    main()

