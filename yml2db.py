#!/usr/bin/env python3

import os
import sys
import re

import getopt
import json

from datetime import datetime

import sqlite3

from lxml import etree

from pprint import pprint

#from signal import signal, SIGPIPE, SIG_DFL  
#signal(SIGPIPE,SIG_DFL)

import yaml
from yaml.loader import SafeLoader

def usage():
    print("Usage : {0} [-o output.json] [input.xml]".format(sys.argv[0]))

def read_yaml(filepath):
    fp = open(filepath, mode="r", encoding="utf-8")
    data = yaml.load(fp, Loader=SafeLoader)
    fp.close()
    return data

def create_table(conn, table) :
    c = conn.cursor()
    sql = 'DROP TABLE IF EXISTS {0};'.format(table)
    c.execute(sql)

    sql = 'CREATE TABLE IF NOT EXISTS {0} ('.format(table)
    sql += 'id INTEGER PRIMARY KEY, '
    sql += 'package TEXT, '
    sql += 'module TEXT, '
    sql += "container TEXT, "
    sql += 'name TEXT, '
    sql += 'value TEXT, '
    sql += 'path TEXT, '
    sql += 'type TEXT '
    sql += ')'

    c = conn.cursor()
    c.execute(sql)

def insert_parameter(conn, table, record) :
    c = conn.cursor()

    sql = 'INSERT INTO {0} VALUES ( NULL, ?, ?, ?, ?, ?, ?, ?);'.format(table)
    items = [
        record['package'],
        record['module'],
        record['container'],
        record['name'],
        record['val'],
        record['path'],
        record['type'],
    ]
    c.execute(sql, items)

def split_key(key) :
    #if re.search(r'/DefinitionRef$', key) :
    #    return

    m = re.search(r'/([\w_]+)/([\w_]+)/(.+)/([\w_]+)', key)
    if m :
        package   = m.group(1)
        module    = m.group(2)
        container = "/" + package + "/" + module + "/" + m.group(3)
        name      = m.group(4)
    else :
        print('ERROR : invalid key, {0}'.format(key), file=sys.stderr)
        sys.exit(1)
    
    record = {
        'package' : package,
        'module' : module,
        'container' : container,
        'name' : name,
    }

    return record

def get_recursively(conn, table, key, data) :
    if isinstance(data, dict) :
        for item in data :
            get_recursively(conn, table, key + "/" + item, data[item])
    elif isinstance(data, list) :
        value_str = ""
        for item in data :
            if isinstance(item, dict) :
                print('dict in list is forbidden')
                sys.exit(1)
            if isinstance(item, list) :
                print('list in list is forbidden')
                sys.exit(1)
            value_str += item + ","
        #print("list : {0}={1}".format(key, value_str))
        record = split_key(key)
        record['val'] = value_str
        record['path'] = key
        record['type'] = ''
        if conn is not None :
            insert_parameter(conn, table, record)
    elif isinstance(data, str) :
        #print('string : {0}={1}'.format(key, data))
        record = split_key(key)
        record['val'] = data
        record['path'] = key
        record['type'] = ''
        if conn is not None :
            insert_parameter(conn, table, record)
    elif isinstance(data, int) :
        #print('int : {0}={1}'.format(key, data))
        record = split_key(key)
        record['val'] = data
        record['path'] = key
        record['type'] = ''
        if conn is not None :
            insert_parameter(conn, table, record)
    else :
        print('unknown data: {0}={1}'.format(key, data))
        sys.exit(1)

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
    conn = None
    
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
    
    table = "params_table"

    if output is not None :
        conn = sqlite3.connect(output)
        create_table(conn, table)
    else :
        fp = sys.stdout

    key = ""
    for filepath in args:
        data = read_yaml(filepath)
        get_recursively(conn, table, key, data)

    if conn is not None :
        conn.commit()
        conn.close()

    print('End')

if __name__ == "__main__":
    main()

