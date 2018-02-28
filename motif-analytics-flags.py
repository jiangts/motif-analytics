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

#because we aren't doing anything really sketchy, we should be able to use global dicts
#to track what we need/want

#room2report is a dictionary that is organized as follows:
#roomID: start time, end time, time in hours, domain, domain, domain, domain
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
	count = 0
	for row in data:	
		count = count + 1
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
	if userAction == "add-session" and roomID not 0:
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
	time = timeStamp[11:13] + '.' + timeStamp[14:16]
	time = float(time)
	print time
	print timeStamp
	if action == "start":
		room2report[roomID].insert(0,time)
	else:
		room2report[roomID].insert(1,time)
	return


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

#creates a simple matplotlib graph for the number of people per room
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

def main():
	response = requests.get(API_URL)
	data = response.json()
	for item in data['query_result']:
		print item		
	iterateRows(data['query_result']['data']['rows'])
	#print room2report
	#people_per_room_dict = countPeoplePerRoom(room2report)
	#print people_per_room_dict
	#userExcel(id2room)
	#graphPeoplePerRoom(people_per_room_dict)

        
if __name__ == '__main__':
    main()
		
