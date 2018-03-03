put your analytics key inside of `~/.bash_profile` for analytics on the entire database, run the motif-analytics-2.py program.

there are six possible inputs of the analytics file:

1. graph users-per-room uses matplotlib to create a histogram that accounts for the number of users in each room

2. graph domains-per-room uses matplotlib to create a histogram that accounts for the number of domains in each room (session)

3. graph time-per-room uses matplotlib to create a histogram that calculates for the minutes each room was opened

4. print domains-by-rank desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the most common domain

5. print users-by-rank-room desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the user that appears in the most rooms

6. print users-by-rank-time desired-length-of-list prints a list from 1 to desired-length-of-list where 1 is the users who has spent the most total minutes using Motif

example of commandline if you want a graph to be generated from the data: python motif-analytics-2.py graph users-per-room

example of commandline if you want a ranked list of length 10 from the data : python motif-analytics-2.py print domains-by-rank 10