# Import the json & requests library
import json
import requests
import sys
import csv
import xlsxwriter
from json2html import *
import pandas as pd
from pandas.io.json import json_normalize
from collections import defaultdict
import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import argparse
import os


API_KEY = os.environ['MOTIF_ANALYTICS_KEY']
API_URL = "https://redash.hugedata.ml/api/queries/4/results.json?api_key=" + API_KEY

		
def dumpclean(obj):
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                dumpclean(v)
            else:
                print '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print v
    else:
        print obj

def dump(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif type(obj) == list:
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)

#going through each row and then using a dict for mapping
#attempting to aggregate data so that you can query by user id and by room
def iterateRows(data, id2room, room2report, room2users):
	count = 0
	for row in data:	
		count = count + 1
		room2users, id2room = decodeRow(row, id2room, room2report, room2users) 
	return room2users, id2room

#each row is a dict where all of the data is stored
def decodeRow(row, id2room, room2report, room2users):
	for key, value in row.iteritems():
		if key == "room-id":
			room2users, id2room = usersPerSession(value, row["user-id"], room2users, id2room)
	return room2users, id2room
			
#dictionary of room2users, now we can see how many users are in each room
#dictionary of id2room so now we can how many sessions an individual user has had
def usersPerSession(roomID, userID, room2users, id2room):
	if roomID in room2users:
		if userID not in room2users[roomID]:
			s = room2users[roomID] 
			s.add(userID)
			room2users[roomID] = s
	else:
		room2users[roomID] = set([userID])
	if userID in id2room:
		if roomID not in id2room[userID]:
			s2 = id2room[userID]
			s2.add(roomID)
			id2room[userID] = s2
	else:
		id2room[userID] = set([roomID])
	return room2users, id2room
			
	
#gets metrics on total number of rooms and the number of people per room	
def countPeoplePerRoom(room2report):
	key_count = 0
	people_per_room_list = defaultdict(int)
	for key, value in room2report.iteritems():
		key_count = key_count + 1
		if (len(room2report[key])) in people_per_room_list:
			x = people_per_room_list[(len(room2report[key]))] + 1 
			people_per_room_list[(len(room2report[key]))] = x
		else:
			people_per_room_list[(len(room2report[key]))] = 1
	#print key_count
	return people_per_room_list
	
def graphPeoplePerRoom(people_per_room_dict):
	values_list = list((people_per_room_dict).values())
	keys_list = list((people_per_room_dict).keys())
	max_users_per_room = max(keys_list)
	y_pos = np.arange(len(keys_list))
	plt.barh(y_pos, values_list, align='center', alpha=0.5)
	plt.yticks(y_pos, keys_list)
	plt.xlabel('Count')
	plt.title('Instances of Room Size')
	plt.show()
	print type(keys_list[0])
	print type(values_list[0])
	
	
#creates an excel spreadsheet where you can see the user and each of the rooms
#that they have been a part of	
def userExcel(id2room):
	workbook = xlsxwriter.Workbook('Motif_UserID_to_Sessions.xlsx')
	worksheet = workbook.add_worksheet()
	row = 0
	col = 0
	worksheet.write(row, col, "user-id")
	worksheet.write(row, col+1, "total-rooms")
	worksheet.write(row, col+2, "room-ids")
	row += 1
	for key, value in id2room.iteritems():
		worksheet.write(row, col, str(key))
		col += 1
		worksheet.write(row, col, len(value))
		for room in value:
			col += 1
			worksheet.write(row, col, str(room))
		row += 1
		col = 0
	workbook.close()
		
def domainsByRank():
	print ("HI")		

#attempt to write out the json to a html file
def create(data):
    scanOutput = json2html.convert(json = data)
    htmlReportFile = 'Report.html'
    with open(htmlReportFile, 'w') as htmlfile:
    	htmlfile.write(str(scanOutput))

#attempt to print out results as a CSV    	
def pandas_try(data):
	df = json_normalize(data)
	df.to_csv('Output.csv')

def main():
	response = requests.get(API_URL)
	data = response.json()
	#print data['query_result']
	room2report = {}
	id2room = defaultdict(set)
	room2users = defaultdict(set)
	for item in data['query_result']:
		print item
	room2report, id2room = iterateRows(data['query_result']['data']['rows'], id2room, room2report, room2users)
	people_per_room_dict = countPeoplePerRoom(room2report)
	userExcel(id2room)
	graphPeoplePerRoom(people_per_room_dict)
	#create(data)
	#pandas_try(data['query_result']['data'])
	#need to decode each row, and then aggregate so that I can sort by session
	#each user will have a list of room numbers, and all room numbers will be stored in a dict, which
	#maps to a list of 
	#dumpclean(data)
	#dump(data)
        
if __name__ == '__main__':
    main()
		
