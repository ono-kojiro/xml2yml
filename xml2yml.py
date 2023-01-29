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

def create_table(conn, table) :
    c = conn.cursor()
    sql = 'DROP TABLE IF EXISTS {0};'.format(table)
    c.execute(sql)

    sql = 'CREATE TABLE IF NOT EXISTS {0} ('.format(table)
    sql += 'id INTEGER PRIMARY KEY, '
    sql += 'package TEXT, '
    sql += 'module TEXT, '
    sql += "container TEXT, "
    sql += 'path TEXT, '
    sql += 'name TEXT, '
    sql += 'type TEXT, '
    sql += 'value TEXT '
    sql += ')'

    c = conn.cursor()
    c.execute(sql)

def insert_parameter(conn, table, package, module, container, path, name, type, val) :
    c = conn.cursor()

    sql = 'INSERT INTO {0} VALUES ( NULL, ?, ?, ?, ?, ?, ?, ?);'.format(table)
    items = [
        package, module, container, path, name, type, val
    ]
    c.execute(sql, items)

def xpath2dict(data, path, val) :

    debug = 0
    if val is not None :
        m = re.search(r'/Ecuc/Os/AppMode', val)
        if m :
            debug = 1

    tokens = re.split(r'/', path)
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

    if val is None :
        cur[token] = {}
    else :
        if val == 'true' :
            val = True
        elif val == 'talse' :
            val = False
        elif val.isdecimal() :
            val = int(val)

        if debug :
            print("path is {2}, token is {0}, val is {1}".format(token, val, path))

        if not token in cur:
            if debug :
                print("  scalar")
            cur[token] = val
        elif type(cur[token]) is list :
            if debug :
                print("  append")
            cur[token].append(val)
        else :
            if debug :
                print("  scalar to list")
            tmp = cur[token]
            cur[token] = [ tmp, val]
    
def get_text(node, nss, tag) :
    text = None
    item = node.find("./ns:{0}".format(tag), nss)
    if item is not None:
        text = item.text
    return text

def get_parameter_values(indent, parent, userdata, container) :
    params = {}

    nss = userdata["nss"]
    conn = userdata["conn"]
    table = userdata["table"]

    package = userdata["package"]
    module  = userdata["module"]

    items = parent.findall("./*/*/ns:DEFINITION-REF/..", nss)
    if items is None :
        return params

    data = {}

    for item in items :
        type_name = get_text(item, nss, "DEFINITION-REF")
        value = get_text(item, nss, "VALUE")
        valref = get_text(item, nss, "VALUE-REF")

        if value is not None:
            pass
        elif valref is not None :
            value = valref
        else :
            value = ''

        name = re.sub(r'.+/', '', type_name)
        
        path = container + "/" + name

        if value != "" :
            pprint(name)
            pprint(params)
            print("DEBUG : value is {0}".format(value))
            if not name in params :
                params[name] = value
            elif type(params[name]) is list :
                params[name].append(value)
            else :
                tmp = params[name]
                params[name] = [ tmp, value]

            if not name in data :
                data[name] = {}
            if not type_name in data[name] :
                data[name][type_name] = None

            if data[name][type_name] is None :
                data[name][type_name] = value
            else :
                data[name][type_name] += ":{0}".format(value)
    
    for name in data :
        for type_name in data[name] :
            value = data[name][type_name]

            path = container + "/" + name

            if conn :
                insert_parameter(conn,
                    table,
                    package,
                    module,
                    container,
                    path,
                    name,
                    type_name,
                    value
                )


    return params

def parse_container(indent, parent, userdata, path) :
    fp = userdata["fp"]
    nss = userdata["nss"]
    data = userdata["data"]

    name   = get_text(parent, nss, "SHORT-NAME")
    defref = get_text(parent, nss, "DEFINITION-REF")
    defref = re.sub(r'.+/', '', defref)

    container = path + "/" + name

    xpath2dict(data, container, None)
    xpath2dict(data, container + "/DefinitionRef", defref)

    params = get_parameter_values(indent + "  ", parent, userdata, container)
    for param in params :
        vals = []
        if type(params[param]) is list :
            vals = params[param]
        else :
            vals = [ params[param] ]
        for val in vals :
            xpath2dict(data, container + "/" + param, val)
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
        name = get_text(parent, nss, "SHORT-NAME")

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
            "hvi:o:d:t:",
            [
                "help",
                "version",
                "output=",
                "database=",
                "table=",
            ]
        )
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    output = None
    database = None
    conn = None

    table = None
    
    for o, a in opts:
        if o == "-v":
            usage()
            sys.exit(0)
        elif o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--output"):
            output = a
        elif o in ("-d", "--database"):
            database = a
        elif o in ("-t", "--table"):
            table = a
        else:
            assert False, "unknown option"
  
    if database is None and table is not None :
        print('no table option with database', file=sys.stderr)
        ret += 1

    if ret != 0:
        sys.exit(1)

    if len(args) == 0 :
        usage()
        sys.exit(1)
    
    if output is not None :
        fp = open(output, mode='w', encoding='utf-8')
    else :
        fp = sys.stdout

    if database is not None :
        conn = sqlite3.connect(database)
        create_table(conn, table)

    indent = ""
    userdata = {
        "count" : 0,
        "conn" : conn,
        "package" : "",
        "module"  : "",
        "nss" : None,
        "fp"  : fp,
        "table" : table,
        "data" : {},
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

    if conn is not None :
        conn.commit()
        conn.close()

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

