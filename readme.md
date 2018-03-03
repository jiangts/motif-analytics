
put your analytics key inside of `~/.bash_profile` for analytics on the entire database, run the motif-analytics-2.py program.

there are six possible inputs to generate data across the entire cohort:

1. graph users-per-room uses matplotlib to create a histogram that accounts for the number of users in each room

2. graph domains-per-room uses matplotlib to create a histogram that accounts for the number of domains in each room (session)

3. graph time-per-room uses matplotlib to create a histogram that calculates for the minutes each room was opened

4. print domains-by-rank desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the most common domain

5. print users-by-rank-room desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the user that appears in the most rooms

6. print users-by-rank-time desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the users who has spent the most total minutes using Motif

example of commandline if you want a graph to be generated from the data: python motif-analytics-2.py graph users-per-room

example of commandline if you want a ranked list of length 10 from the data : python motif-analytics-2.py print domains-by-rank 10

there are also four "user-query" options:
  total-time, room-count, room-ids, average-time
  
 an example of running a specific user query is as follows:
 
 python motif-analytics-2.py user-query total-time 58fa64cfe0d3ee1097943664
 
total-time: adds the entire length of all the rooms that the user has added-sessions to
room-count: counts the number of rooms that the user has added a session to 
room-ids: all the rooms that a user has added-sessions to
average-time: total-time/room-count

