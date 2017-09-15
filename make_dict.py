import sys
import pymysql
import re
import requests
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

def fix_list(list):
    #x returns a list with a single string elt, so to access call[0], then encode to ascii so you get a ascii string and not unicode
    #also for x in list doesnt work, as it gets a copy. When using range/xrange it directly modifies list
    for x in xrange(len(list)):
        list[x] = list[x].contents[0].encode("ascii").strip()
    return list

def find_info(id_name, soup):
    #find_all syntax: ("TAG", {attr_type: attr_name})
    return fix_list(soup.find_all("span", {"id": id_name}))

def dateify(list_of_dates):
    out_list = []
    for old_date in list_of_dates:
        #try to convert it into a date, if this doesnt work then add to list as ERROR then remove later
        #we remove later because we want to make sure that the start and end dates line up
        try:
            new_date = dt.strptime(old_date, "%m/%d/%Y").date()
            out_list.append(new_date)
        except ValueError:
            out_list.append("ERROR")
    return out_list

def fetch_info(n_number,year):
    #print statement so we know what flight number we are working on
    print("Fetching for %s" % n_number)
    flight_year = int(year)
    #create url to visit
    base_url = "http://registry.faa.gov/aircraftinquiry/NNum_Results.aspx?NNumbertxt="
    full_url = base_url + n_number
    page = requests.get(full_url)

    #get page source in html
    soup = BS(page.content, "lxml")
    
    current_manufacturer = find_info("content_lbMfrName",soup)
    current_model = find_info("content_Label7",soup)
    current_start_date = dateify(find_info("content_lbCertDate",soup))
    current_end_date = dateify(find_info("content_Label9",soup))

    #need[0] since find_info returns a  lists
    current_status = []
    #if len = 0 then the n_number is NOT in use right now, or n_number doesnt exist
    #make sure to get rid of errors in the data
    if len(current_manufacturer) != 0 and current_start_date[0] != "ERROR" and current_end_date[0] != "ERROR":
        current_status.append([current_manufacturer[0],current_model[0],current_start_date[0],current_end_date[0]])

    dereg_manufacturers = find_info(re.compile("content_drptrDeRegAircraft_lbDeRegMfrName_[0-9]"),soup)
    dereg_models = find_info(re.compile("content_drptrDeRegAircraft_lbDeRegModel_[0-9]"),soup)
    dereg_start_dates = dateify(find_info(re.compile("content_drptrDeRegAircraft_lbDeRegCertDate_[0-9]"),soup))
    dereg_end_dates = dateify(find_info(re.compile("content_drptrDeRegAircraft_lbDeRegCancelDate_[0-9]"),soup))

    dereg_status = []
    #if len = 0 then there was NOT history before the current one, or n_number doesnt exist
    if len(dereg_manufacturers) != 0:
        #tuple unpacking, each list should have 4 elts, zip function goes through all 4 in parallel rather than through each one individually
        for a,b,c,d in zip(dereg_manufacturers,dereg_models,dereg_start_dates,dereg_end_dates):
            #if ERROR, then don't include 
            if c == "ERROR" or d == "ERROR":
                continue
            #if end >= 2003 then keep since 2003 is the most recent data we have
            if d.year >= 2003:
                dereg_status.append([a,b,c,d])

    #now we have all the flight history for this n_number since 2003
    n_number_history = current_status + dereg_status
    
    correct_info = []
    for entry in n_number_history:
        start = entry[2].year
        end = entry[3].year
        if isinstance(start, basestring) or isinstance(end, basestring):
            continue
        #if the next is true then it did fly this year, return the manufacturer name and plane number
        if flight_year > start and flight_year < end:
            correct_info.append(entry[0])
            correct_info.append(entry[1])
            break
    return correct_info

def load_dictionary(year):
    #read in local dict
    #format: n-number?manufacturer,plane model,start,end?...

    read_dict = open('dictionary'+year+'.txt', "r")
    #create dictionary
    hash = {}
    #read each line of the dictionary into a list
    lines = read_dict.readlines()
    for x in lines:
        x = x.strip('\n')
        x = x.split('?')
        key = x[0]
        val = []
        #next line in case theres no info
        for a in xrange(1,len(x)):
            # temp = x[a].split(',')
            # val.append(temp)
            val = x[1].split(',')
        hash[key] = val
    read_dict.close()
    return hash

def main():
    #connect to db
    db = db_connect()
    cursor = db.cursor()

    print 'Connected to DB.\n'
    #year = "2009"

    #ask which table to update
    year = raw_input("Enter Table year to build dictionary for: ")
    table = "Flight_Table_" + year

    print 'Querying...\n'
    query = "SELECT distinct Tail_Number FROM " + table
    cursor.execute(query)

    #print 'Query Successful, loading dictionary.\n'

    #for debugging purposes (or if it gets interrupted), if you load the dictionary and stuff is missing then the dictionary is not complete
    hash = load_dictionary(year)

    print 'Dictionary loaded'
    #hash = {}

    for entry in cursor:

        n_number = str(entry[0]) #to ensure its actually a str
        
        #make sure the n_number is valid
        if n_number == '' or n_number[0] != 'N' or n_number[1] == '-':
            continue

        if n_number not in hash:
            info = fetch_info(n_number,year)
            hash[n_number] = info
            fileout = open('dictionary'+year+'.txt','a')
            out = n_number
            if len(info) != 0:
                out += '?'+info[0]+','+info[1]
            out += '\n'
            fileout.write(out)
            fileout.close()

if __name__ == '__main__':
    main()
#     fetch_info('N368NB',2010)