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
from datetime import datetime
import time


API_KEY = os.environ['MOTIF_ANALYTICS_KEY']
API_URL = "https://redash.hugedata.ml/api/queries/4/results.json?api_key=" + API_KEY

#because we aren't doing anything really sketchy, we should be able to use global dicts
#to track what we need/want

#room2report is a dictionary that is organized as follows:
#roomID: start time, end time, domain, domain, domain, domain... all domains
#to find the users that were in that room you can use the room2users dictionary
room2report = defaultdict(list)
#userID maps to a set of all the rooms that it is associated with, so we can
#see who our most active users are
id2room = defaultdict(set)
#roomID maps to a set of all the userIDs that were associated with that room
#throughout the lifetime of the room
room2users = defaultdict(set)

#going through each row and then using a dict for mapping
#attempting to aggregate data so that you can query by user id and by room
def iterateRows(data):
	for row in data:
		decodeRow(row)
	return

#by iterating through the data one time, we should capture all of the relevant 
#information into a dictionary
def decodeRow(row):
	#need to check the action before doing anything because some of the 
	#data are missing pieces... if "open-room" there is no "room-id" yet and
	#"origin" is only guaranteed to appear during an "add-session" call
	userAction = row["method"]
	userID = row["user-id"]
	if userAction == "open-room":
		roomID = 0
	else:
		roomID = row["room-id"]
	if userAction == "add-session" and roomID != 0:
		domainName = row["origin"]
		room2report[roomID].append(domainName)
	timeStamp = row["createdAt"]
	
	#generate all roomID to a list of users that are in the room
	if roomID in room2users:
		#since the room is already in existence, we need to check to see 
		#if the room is being closed
		if userAction == "close-room":
			calculateRoomTime(roomID, timeStamp, "end")
		if userID not in room2users[roomID]:
			s = room2users[roomID] 
			s.add(userID)
			room2users[roomID] = s
	else:
		#if the roomID is not already stored, it is new, and we need to create a start date
		room2users[roomID] = set([userID])
		calculateRoomTime(roomID, timeStamp, "start")
	#generate all userID to list of rooms they are a part of 
	if userID in id2room:
		if roomID not in id2room[userID]:
			s2 = id2room[userID]
			s2.add(roomID)
			id2room[userID] = s2
	else:
		id2room[userID] = set([roomID])
	return

#stores the room time in the 0 and 1 index of the room2report dictionary
#at the 0 is the start time (when the room id is assigned) and at the 
#1 is the end time of the room	
def calculateRoomTime(roomID, timeStamp, action):
	#time = timeStamp[11:13] + '.' + timeStamp[14:16]
	#time = float(time)
	print timeStamp
	timeStamp = timeStamp[0:8] + ' ' +timeStamp[9:]
	print timeStamp
	fmt = '%Y-%m-%d %H:%M:%S.%f'
	d1 = datetime.strptime(timeStamp, fmt)
	d1_ts = time.mktime(d1.timetuple())
	if action == "start":
		#room2report[roomID].insert(0,time)
		room2report[roomID].insert(0,d1_ts)
	else:
		#room2report[roomID].insert(1,time)
		room2report[roomID].insert(1,d1_ts)
	return

#gets metrics on total number of rooms and the number of people per room	
def countPeoplePerRoom():
	key_count = 0
	people_per_room_list = defaultdict(int)
	for key, value in room2users.iteritems():
		key_count = key_count + 1
		if (len(room2users[key])) in people_per_room_list:
			x = people_per_room_list[(len(room2users[key]))] + 1 
			people_per_room_list[(len(room2users[key]))] = x
		else:
			people_per_room_list[(len(room2users[key]))] = 1
	return people_per_room_list

#creates a simple matplotlib graph for the number of people per room
def graphRoom(people_per_room_dict):
	values_list = list((people_per_room_dict).values())
	keys_list = list((people_per_room_dict).keys())
	max_users_per_room = max(keys_list)
	y_pos = np.arange(len(keys_list))
	plt.barh(y_pos, values_list, align='center', alpha=0.5)
	plt.yticks(y_pos, keys_list)
	plt.xlabel('Count')
	plt.title('Instances')
	plt.show()
	print type(keys_list[0])
	print type(values_list[0])
	
#this is the length of each row of room2report minus 2 (which are the start & end
#times) 
def domainsPerRoom():
	room_list = defaultdict(int)
	for key, value in room2report.iteritems():
		if (len(room2report[key])-2) in room_list:
			x = room_list[(len(room2report[key]))] + 1 
			room_list[(len(room2report[key]))] = x
		else:
			room_list[(len(room2report[key]))-2] = 1
	return room_list

#used for rounding the minutes to the nearest 5 minutes
def myround(x, base=5):
    return int(base * round(float(x)/base))
	
#calculates the average amount of time spent in each room in question
def timePerRoom():
	time_list = defaultdict(int)
	for key, value in room2report.iteritems():
		d1_ts = value[0]
		if len(value) > 1 and isinstance(value[0], float):
			if isinstance(value[1], float):
				d2_ts = value[1]
				relevantTime = int(d2_ts-d1_ts) / 60
				print relevantTime
				#relevantTime = myround(openTime)
			else: relevantTime = -10
		else:
			relevantTime = -10
		if relevantTime in time_list:
			x = time_list[relevantTime] + 1 
			time_list[relevantTime] = x
		else:
			time_list[relevantTime] = 1
	return time_list

def main():
	response = requests.get(API_URL)
	data = response.json()
	for item in data['query_result']:
		print item		
	iterateRows(data['query_result']['data']['rows'])
	#working with args
	
def dont():
	args = sys.argv
	if args[1] == "graph":
		if args[2] == "users-per-room":
			pDict = countPeoplePerRoom()
			graphRoom(pDict)
		elif args[2] == "domains-per-room":
			dDict = domainsPerRoom()
			graphRoom(dDict)
		elif args[2] == "time-per-room":
			tDict = timePerRoom()
			graphRoom(tDict)
		else:
			print("You did not imput a valid graphing request, acceptable requests are")
			print ('\n')
			print ("1. users-per-room")
			print ('\n')
			print ("2. domains-per-room")
			print ('\n')
			print ("3. time-per-room")
			print ('\n')
	elif args[1] == "print":
		"hi"
	return
		
	#command line arguments:
	#two options: graph or print
	#graph options: 1. users-per-room 2. domains-per-room 3. time-per-room
	#print options: 4. domains-by-rank, 5. users-by-rank 
        
if __name__ == '__main__':
    main()
		