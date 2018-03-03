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

room2domain = defaultdict(list)
room2timeStamp = defaultdict(list)
#userID maps to a set of all the rooms that it is associated with, so we can
#see who our most active users are
id2room = defaultdict(set)
#roomID maps to a set of all the userIDs that were associated with that room
#throughout the lifetime of the room
room2users = defaultdict(set)

#going through each row and then using a dict for mapping
#attempting to aggregate data so that you can query by user id and by room
def iterateRows(data):
	count_int = int(0)
	count = 0
	count_int_2 = int(0)
	for row in data:
		count += 1
		count_int, count_int_2 = decodeRow(row, count_int, count_int_2)
	#print "num add sessions: "
	#print count_int
	#print "num close room: "
	#print count_int_2
	#print "total count: "
	#print count
	return

#by iterating through the data one time, we should capture all of the relevant 
#information into a dictionary
def decodeRow(row, count_int, count_int_2): 
	#need to check the action before doing anything because some of the 
	#data are missing pieces... if "open-room" there is no "room-id" yet and
	#"origin" is only guaranteed to appear during an "add-session" call
	userAction = row["method"]
	if userAction == "open-room" or userAction == "join-room" or userAction == "leave-room" or userAction == "open-or-join" or userAction == "get-room":
		return int(count_int), int(count_int_2)
	roomID = row["room-id"]
	timeStamp = row["createdAt"]
	userID = row["user-id"]
	if userAction == "add-session":
		count_int += 1
		calculateRoomTime(roomID, timeStamp)
		domainName = row["origin"]
		room2domain[roomID].append(domainName)
	#since the room is already in existence, we need to check to see 
	#if the room is being closed
	elif userAction == "close-room":
		calculateRoomTime(roomID, timeStamp)
		count_int_2 += 1
	#generate all roomID to a list of users that are in the room
	if roomID in room2users:
		if userID not in room2users[roomID]:
			room2users[roomID].add(userID)
	else:
		#if the roomID is not already stored, it is new, and we need to create a start date
		room2users[roomID] = set([userID])
	#generate all userID to list of rooms they are a part of 
	if userID in id2room:
		if roomID not in id2room[userID]:
			id2room[userID].add(roomID)
	else:
		id2room[userID] = set([roomID])
	 
	return int(count_int), int(count_int_2)

#stores the room time in the 0 and 1 index of the room2report dictionary
#at the 0 is the start time (when the room id is assigned) and at the 
#1 is the end time of the room	
def calculateRoomTime(roomID, timeStamp):
	#time = timeStamp[11:13] + '.' + timeStamp[14:16]
	#time = float(time)
	#timeStamp example: 2018-02-28T09:04:11.310000
	timeStamp = timeStamp[0:10] + ' ' +timeStamp[11:19]
	fmt = '%Y-%m-%d %H:%M:%S'
	#print timeStamp
	d1 = datetime.strptime(timeStamp, fmt)
	room2timeStamp[roomID].append(d1)
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
def graphRoom(people_per_room_dict, x_axis_label, y_axis_label, title_label):
	values_list = list((people_per_room_dict).values())
	keys_list = list((people_per_room_dict).keys())
	max_users_per_room = max(keys_list)
	y_pos = np.arange(len(keys_list))
	plt.barh(y_pos, values_list, align='center', alpha=0.5)
	plt.yticks(y_pos, keys_list)
	plt.xlabel(x_axis_label)
	plt.ylabel(y_axis_label)
	plt.title(title_label)
	plt.show()
	
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
	
#finds the length of time that a room was opened by calculating the difference
#between the first and the last timestamp recorded by an add-session or close-room
def lengthOpened(roomID):
	timesList = room2timeStamp[roomID]
	if len(timesList) > 1:
		d1 = min(timesList)
		d2 = max(timesList)
		diff = d2 - d1
		minutes = (diff.seconds) / 60
		return minutes
	else:
		return 0
		
#calculates the average amount of time spent in each room in question
def timePerRoom():
	time_list = defaultdict(int)
	count_int = 0
	for key, value in room2timeStamp.iteritems():
		if len(value) > 1:
			count_int += 1
			#print count_int
			d1 = min(value)
			d2 = max(value)
			#print [d1, d2]
			diff = d2 - d1
			minutes = (diff.seconds) / 60
			#print (str(minutes) + ' Minutes')
			relevantTime = minutes
			if relevantTime > 60:
				relevantTime = 60
		else:
			relevantTime = "-inf" #there is no end time
		if relevantTime in time_list:
			x = time_list[relevantTime] + 1 
			time_list[relevantTime] = x
		else:
			time_list[relevantTime] = 1
	print "at least two timestamps" 
	print count_int
	return time_list
	
def keyWithMaxVal(d):
    #a) create a list of the dict's keys and values; 
    #b) return the key with the max value
	v=list(d.values())
	k=list(d.keys())
	return k[v.index(max(v))]
	
def rankByAppearance(input, desiredLength):
	returnList = range(desiredLength)
	if input == "domains":
		domains_dict = defaultdict(int)
		#use the room2domain
		for key, value in room2domain.iteritems():
			for v in value:
				if v in domains_dict:
					s = domains_dict[v] + 1
					domains_dict[v] = s
				else:
					domains_dict[v] = 1
		for x in range(desiredLength):
			keyToRemove = keyWithMaxVal(domains_dict)
			returnList[x] = keyToRemove
			domains_dict.pop(keyToRemove)
		return returnList
	elif input == "users":
		users_dict = defaultdict(int)
		for key, value in id2room.iteritems():
			roomCount = len(value)
			users_dict[key] = roomCount
		for x in range(desiredLength):
			keyToRemove = keyWithMaxVal(users_dict)
			returnList[x] = keyToRemove
			users_dict.pop(keyToRemove)
		return returnList

def printList(a_list):
	for x in range(len(a_list)):
		string_x = str((x + 1))
		one_line =  string_x + "." + str(a_list[x])
		print one_line
		
def rankByTime(desiredLength):
	returnList = range(desiredLength)
	user2time = defaultdict(int)
	for key, value in id2room.iteritems():
		#for each room that was here, we need to find the length of time the room 
		#was opened, and add it to the running total of minutes for the user in the 
		#user2time dict
		runningTotal = 0
		for roomID in value:
			runningTotal = runningTotal + lengthOpened(roomID)
		user2time[key] = runningTotal
	for x in range(desiredLength):
		keyToRemove = keyWithMaxVal(user2time)
		returnList[x] = keyToRemove
		user2time.pop(keyToRemove)
	return returnList

def main():
	response = requests.get(API_URL)
	data = response.json()
	#for item in data['query_result']:
		#print item		
	iterateRows(data['query_result']['data']['rows'])
	#print room2report
	#working with args
	
#def dont():
	args = sys.argv
	if args[1] == "graph":
		if args[2] == "users-per-room":
			pDict = countPeoplePerRoom()
			graphRoom(pDict, "Count", "Number of Users", "Users per Room")
		elif args[2] == "domains-per-room":
			dDict = domainsPerRoom()
			graphRoom(dDict, "Count", "Number of Domains", "Domains per Room")
		elif args[2] == "time-per-room":
			tDict = timePerRoom()
			graphRoom(tDict, "Count", "Time (min)", "Minutes per Room")
		else:
			print("You did not imput a valid graphing request, acceptable requests are: ")
			print ('\n')
			print ("1. users-per-room")
			print ('\n')
			print ("2. domains-per-room")
			print ('\n')
			print ("3. time-per-room")
			print ('\n')
	elif args[1] == "print":
		if len(args) > 3:
			desiredLength = int(args[3])
		if args[2] == "domains-by-rank":
			a_list = rankByAppearance("domains", desiredLength)
			printList(a_list)
		elif args[2] == "users-by-rank-room":
			a_list = rankByAppearance("users", desiredLength)
			printList(a_list)
		elif args[2] == "users-by-rank-time":
			a_list = rankByTime(desiredLength)
			printList(a_list)
		else:
			print("You did not imput a valid printing request, acceptable requests are: ")
			print ('\n')
			print ("1. domains-by-rank")
			print ('\n')
			print ("2. users-by-rank-room")
			print ('\n')
			print ("3. users-by-rank-time")
			print ('\n')
	return
		
	#command line arguments:
	#two options: graph or print
	#graph options: 1. users-per-room 2. domains-per-room 3. time-per-room
	#print options: 4. domains-by-rank, 5. users-by-rank-room, 6. users-by-rank-time, optional third arg of a list of
	#how long you want the printed list to be
        
if __name__ == '__main__':
    main()
		
