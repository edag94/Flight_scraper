import sys
import pymysql
import re
import requests
from bs4 import BeautifulSoup as BS
from datetime import datetime as dt
from make_dict import db_connect, load_dictionary

""" Database information """
username = "--REDACTED--"
password = "--REDACTED--"
database = "--REDACTED--"
host = "--REDACTED--"


def main():
    #connect to db
    db = db_connect()
    cursor = db.cursor()

    print 'Connected to DB.\n'

    #year = "2009"

    #ask which table to update
    year = raw_input("Enter year for SQL: ")
    table = "Flight_Table_"+ year

    print 'Querying...\n'
    query = "SELECT distinct Tail_Number FROM " + table
    cursor.execute(query)

    print 'Query Successful, loading dictionary.\n'

    hash = load_dictionary(year)

    print 'Dictionary loaded, creating SQL file'
        
    for entry in cursor:
        n_number = str(entry[0]) #to ensure its actually a str
        
        #make sure the n_number is valid
        if n_number == '' or n_number[0] != 'N' or n_number[1] == '-':
            continue
        n_number_info = []
        try:
            n_number_info = hash[n_number]
        except:
            file = open('error.txt', 'a')
            file.write(n_number + '\n')
            file.close()
            continue

        if len(n_number_info) != 0:
            #construct SQL queries
            query = "UPDATE " + table + " Set Manufacturer_name = \'" + n_number_info[0] + "\', Plane_model = \'" + n_number_info[1] + "\' Where Tail_number = \'" + n_number + "\';"
            query += "\n"
            file = open("out" + year + ".txt", 'a')
            file.write(query)
            file.close()

if __name__ == '__main__':
    main()
