'''
Created on May 30, 2017

@author: home
'''


import sys
import pymysql
import re
import requests
import time
from bs4 import BeautifulSoup as BS
from datetime import datetime as dt

""" Database information """
username = "--REDACTED--"
password = "--REDACTED--"
database = "--REDACTED--"
host = "--REDACTED--"

def db_connect():
    db = pymysql.connect(user = username, passwd = password, db = database, host = host)
    return db

def main():
    #connect to db
    db = db_connect()
    cursor = db.cursor()

    #year = '2010'
    name = raw_input("Enter txt filename to execute: ")

    file = open(name + '.txt', 'r')
    lines = file.readlines()
    query = ''
    print('building query \n')
    for x in lines:
        temp = x.strip('\n')
        temp += ' '
        query += temp
    print('executing query\n')
    cursor.execute(query)
    db.commit()
    file.close()


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))