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

def usage():
    print("Usage : {0} [-o output.json] target.db reference.db".format(sys.argv[0]))

def str2int(s) :
    m = re.search(r'^0(x|X)', s)
    if m :
        val = int(s, 16)
        return val
    
    m = re.search(r'^(\d+)(u|U)$', s)
    if m :
        val = int(m.group(1))
        return val

    if s.isdecimal() :
        val = int(s)
        return val

    return None

def compare_as_int(str1, str2) :
    ret = 0

    val1 = str2int(str1)
    val2 = str2int(str2)

    if val1 is None or val2 is None :
        ret = 1
    elif val1 != val2 :
        ret = 1
    
    return ret

def check_modified(conn) :
    sql  = "SELECT "
    sql +=   "tar_db.params_table.path AS path, "
    sql +=   "tar_db.params_table.type AS type, "
    sql +=   "tar_db.params_table.value AS tar_val, "
    sql +=   "ref_db.params_table.value AS ref_val "
    sql += "FROM tar_db.params_table "
    sql += "  INNER JOIN ref_db.params_table ON tar_db.params_table.path = ref_db.params_table.path "
    sql += "ORDER BY path ASC "
    sql += ";"
    c = conn.cursor()
    rows = c.execute(sql)

    ok = 0
    ng = 0

    for row in rows :
        #print(str(row))
        path = row['path']
        type_name = row['type']
        tar_val = row['tar_val']
        ref_val = row['ref_val']
        if tar_val == ref_val :
            ok += 1
        else :
            ret = compare_as_int(tar_val, ref_val)
            if ret == 0 :
                ok += 1
            else :
                print("MODIFIED : {0}, {1}, {2}, {3}".format(tar_val, ref_val, path, type_name))
                ng += 1

    #print("ok : {0}".format(ok))
    #print("ng : {0}".format(ng))


def check_removed(conn) :
    sql  = "SELECT "
    sql +=   "tar_db.params_table.path AS tar_path, "
    sql +=   "tar_db.params_table.value AS tar_val, "
    sql +=   "ref_db.params_table.path AS ref_path "
    sql += "FROM tar_db.params_table "
    sql += "  LEFT JOIN ref_db.params_table ON tar_db.params_table.path = ref_db.params_table.path "
    sql += "WHERE ref_path IS NOT NULL "
    sql += "ORDER BY tar_path ASC "
    sql += ";"
    c = conn.cursor()
    rows = c.execute(sql)

    for row in rows :
        #print(str(row))
        tar_path = row['tar_path']
        tar_val  = row['tar_val']
        print("REMOVED : {0}, {1}".format(tar_val, tar_path))

def check_added(conn) :
    sql  = "SELECT "
    sql +=   "ref_db.params_table.path AS ref_path, "
    sql +=   "ref_db.params_table.value AS ref_val, "
    sql +=   "tar_db.params_table.path AS tar_path "
    sql += "FROM ref_db.params_table "
    sql += "  LEFT JOIN tar_db.params_table ON tar_db.params_table.path = ref_db.params_table.path "
    sql += "WHERE tar_path IS NOT NULL "
    sql += "ORDER BY ref_path ASC "
    sql += ";"
    c = conn.cursor()
    rows = c.execute(sql)

    for row in rows :
        #print(str(row))
        ref_path = row['ref_path']
        ref_val  = row['ref_val']
        print("ADDED : {0}, {1}".format(ref_val, ref_path))

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

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    if len(args) != 2 :
        usage()
        sys.exit(1)

    dbs = [ 'tar_db', 'ref_db']
    for i in range(len(dbs)) :
        db = dbs[i]
        filepath = args[i]

        filename = os.path.basename(filepath)
        basename = os.path.splitext(filename)[0]
        c = conn.cursor()

        sql = "ATTACH DATABASE '{0}' AS '{1}';".format(filepath, db)
        print(sql)
        c.execute(sql)

    check_added(conn)
    check_modified(conn)
    check_removed(conn)
        
    conn.close()

    if output is not None :
        fp.close()
    
if __name__ == "__main__":
    main()

