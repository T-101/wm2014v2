# -*- coding: utf-8 -*-

# http://stats.iihf.com/hydra/2014-wm/widget_en_2014_wm_live_ticker_game_18.html

import requests
import bs4
import os
import io
import re
import time

from sys import exit

from bs4 import BeautifulSoup

channels = []

cachedir = 'wm2014_cache'

games = ['21']

waiter = 0
timerClock = 0
gameAnnounced = False

gamestatus = {'not played': '-1', 'endgame': '666'}

periods = {'1st': False, '2nd': False, '3rd': False, 'OT': False, 'GWS': False}

teamDict = { 'GER': 'Germany', 'FIN': 'Finland', 'NOR': 'Norway', 'SWE': 'Sweden', 'KAZ': 'Kazakhstan', 'BLR': 'Belarus', 'CAN': 'Canada', 'CZE': 'Czech Republic', 'DEN': 'Denmark', 'FRA': 'France',
'ITA': 'Italy', 'LAT': 'Latvia', 'RUS': 'Russia', 'SUI': 'Switzerland', 'SVK': 'Slovakia', 'USA': 'United States' }

goaltypes = {'ENG': 'Empty net goal', 'EQ': 'Equal strength', 'PP1': 'One man powerplay', 'PP2': 'Two man powerplay', 'SH1': 'Shorthanded goal', 'SH2': 'Two man shorthanded goal', 'PS': 'Penalty shot', 'EQ-EA': 'Equal Strength', 'PP1-ENG': 'One man powerplay, Empty net goal'}

eventID = -1
eventCount = -1

def getGame(game):
	global eventID, eventCount
	eventID = -1
	eventCount = -1
	if not os.path.exists(cachedir): os.makedirs(cachedir)
	if not os.path.exists(cachedir+'/'+game):
		f = open(cachedir+'/'+game, 'w')
		f.write('{}'.format(eventID))
		f.close()
	else:
		f = open(cachedir+'/'+game, 'r')
		eventID = f.read()
		f.close()
		eventID = int(eventID)
	httpdata = requests.get('http://stats.iihf.com/hydra/2014-wm/widget_en_2014_wm_live_ticker_game_'+game+'.html')
	if httpdata.status_code != 200: return "404"

# get rid of the \"-wtf in the classnames
	fixed = re.sub(r'\\"', r'"', httpdata.text)
	return BeautifulSoup(fixed)



def writeCache(game):
	global eventID
	f = open(cachedir+'/'+game, 'w')
	f.write('{}'.format(eventID))
	f.close()



def endGameStats(event):

	homeShotsPer = event.div.find_all("div")[3].find_all('span', {'class' : 'left'})[0].string
	homeShots = event.div.find_all("div")[4].span.span.next_element.next_element
	homeShotsPeriod = event.div.find_all("div")[4].find_all('span')[1].string
	homeSavesPer = event.div.find_all("div")[5].find_all('span', {'class' : 'left'})[0].string
	homeSaves = event.div.find_all("div")[6].find_all('span', {'class' : 'left'})[0].string
	homePIM = event.div.find_all("div")[7].find_all('span', {'class' : 'left'})[0].string

	awayShotsPer = event.div.find_all("div")[3].find_all('span', {'class' : 'right'})[0].string
	awayShots2 = re.sub('<[^<]+?>', '', str(event.div.find_all("div")[4].find_all('span')[3]))
	awayShots = re.sub(r'\([^)]*\)', '', awayShots2)
	awayShotPeriod = event.div.find_all("div")[4].find_all('span')[4].string
	awaySavesPer = event.div.find_all("div")[5].find_all('span', {'class' : 'right'})[0].string
	awaySaves = event.div.find_all("div")[6].find_all('span', {'class' : 'right'})[0].string
	awayPIM = event.div.find_all("div")[7].find_all('span', {'class' : 'right'})[0].string
	
	period1Goals = event.div.find_all("div")[8].find_all('span', {'class' : 'result'})[0].string
	period2Goals = event.div.find_all("div")[9].find_all('span', {'class' : 'result'})[0].string
	period3Goals = event.div.find_all("div")[10].find_all('span', {'class' : 'result'})[0].string
	periodOTGoals = event.div.find_all("div")[11].find_all('span', {'class' : 'result'})[0].string
	periodSOGoals = event.div.find_all("div")[12].find_all('span', {'class' : 'result'})[0].string
	
	teams = event.find_all("span", {"class" : 'countries'})[0].string
	homeTeam = str(teams).split('-')[0].strip()
	awayTeam = str(teams).split('-')[1].strip()
	scoring = event.find_all("span", {"class" : 'result'})[0].string
	
	gameGoals = (period1Goals+', '+period2Goals+', '+period3Goals)
	if periodOTGoals != '-': gameGoals += (', '+periodOTGoals)
	if periodSOGoals != '-': gameGoals += (', '+periodSOGoals)
	
	return (str(teamDict[homeTeam]+' - '+teamDict[awayTeam]+':  '+scoring+'  ('+gameGoals+')'),
		str(teamDict[homeTeam]+' saves: '+homeSaves+' ('+homeSavesPer+'), shots: '+homeShots+' ('+homeShotsPer+'), PIM: '+homePIM+'. '+teamDict[awayTeam]+' saves: '+awaySaves+' ('+awaySavesPer+'), shots: '+awayShots+' ('+awayShotsPer+'), PIM: '+awayPIM))



def checkGameStart(event):

	global gameAnnounced

	try:
		if event.tbody.find_all('tr')[0].find_all('td', {'class' : 'col2'})[0].string == 'GK in':
			if event.tbody.find_all('tr')[1].find_all('td', {'class' : 'col2'})[0].string == 'GK in':
				if event.tbody.find_all('tr')[1].find_all('td', {'class' : 'col1'})[0].string == '00:00':
					if gameAnnounced == False: return True
		else: return False
	except IndexError: return false



def checkEndGame(event):

	global gameAnnounced

	gameEnded = False

	try:
		period1Status = event.div.find_all("div")[8].find_all('span', {'class': 'status-text'})[0].string
	except IndexError: period1Status = None
	try:
		period2Status = event.div.find_all("div")[9].find_all('span', {'class': 'status-text'})[0].string
	except IndexError: period2Status = None
	try:
		period3Status = event.div.find_all("div")[10].find_all('span', {'class': 'status-text'})[0].string
	except IndexError: period3Status = None
	periodOTStatus = event.div.find_all("div")[11].find_all('span', {'class': 'status-text'})[0].string
	periodSOStatus = event.div.find_all("div")[12].find_all('span', {'class': 'status-text'})[0].string

# check for endgame
	if period3Status == 'finished':
		if periodOTStatus == 'not played' or periodOTStatus == 'finished':
			if periodSOStatus == 'not played' or periodSOStatus == 'finished':
				gameEnded = True
				gameAnnounced = False

# redundance check for endgame, because slacking iihf stats not always adding 'finished' to third period
	try:
		if event.tbody.find_all('tr')[0].find_all('td', {'class' : 'col2'})[0].string == 'GK out':
			if event.tbody.find_all('tr')[1].find_all('td', {'class' : 'col2'})[0].string == 'GK out':
				gameEnded = True
				gameAnnounced = False
	except IndexError: gameEnded = False

	return gameEnded


def parseEvent(event, index):
	global eventID, eventCount

	print (eventID, eventCount)

	try:
		eventTime = event.tbody.find_all('tr')[index].find_all('td', {'class' : 'col1'})[0].string
	except IndexError:
		return (-1, '')
	eventType = event.tbody.find_all('tr')[index].find_all('td', {'class' : 'col2'})[0].string
	eventCountry = event.tbody.find_all('tr')[index].find_all('td', {'class' : 'col3'})[0].string
	eventPlayer = event.tbody.find_all('tr')[index].find_all('td', {'class' : 'col4'})[0].string.replace('.', '#')
	eventReason = event.tbody.find_all('tr')[index].find_all('td', {'class' : 'col5'})[0].string
	
	if eventTime == None:
		return (-1, '')

# sanitize
	if eventReason == None: eventReason = ""
	else: eventReason = ('('+eventReason.replace(u'\xa0', u'')+')')
	if eventType == None: eventType = ''
	else: eventType = eventType.replace(u'\xa0', '')
		
# get goalie event
	if eventType == "GK in" or eventType == "GK out":
		eventCount += 1
		if eventCount > eventID:
			returnoutput = (eventTime+'  '+eventType.ljust(8)+eventCountry+' '+eventPlayer)
			eventID += 1
			return (0, returnoutput)
		else: return (-1, '')

# get goal or penalty event
	try:
		if event.tbody.find_all('tr')[index+1].find_all('td', {'class' : 'col1'})[0].string == None:
			eventAssist1 = (event.tbody.find_all('tr')[index+1].find_all('td', {'class' : 'col4'})[0].string).split()[-2].title()
			eventAssist = True
		else: eventAssist = False
	except IndexError:
		eventAssist = False
	try:
		if event.tbody.find_all('tr')[index+2].find_all('td', {'class' : 'col1'})[0].string == None and eventAssist == True:
			eventAssist2 = (event.tbody.find_all('tr')[index+2].find_all('td', {'class' : 'col4'})[0].string).split()[-2].title()
			eventAssists = True
		else: eventAssists = False
	except IndexError:
		eventAssists = False
	if eventTime != None:
		eventCount += 1
		if eventAssist == True:	eventReason = eventAssist1
		if eventAssists == True: eventReason = eventReason+', '+eventAssist2
		if eventAssist == True: eventReason = '('+eventReason+')'

		if eventType.split()[-1] != "min" and eventType != 'PS':
			goalType = eventType.split()[-1].strip()
			eventType = eventType.split()[0]
			try:
				eventReason += str(' ('+goaltypes[goalType]+')')
			except KeyError: pass
			eventString = '*GOAL*'
		else:
			eventString = 'PENALTY'

		if eventCount > eventID:
			returnoutput = str(eventTime+' '+eventString.ljust(8)+'  '+eventType.ljust(8)+eventCountry+' '+eventPlayer+' '+eventReason)
			eventID += 1

			return (0, returnoutput)
	return (-1, '')


def getScores(game, bot, user, channel, args):
	global waiter, channels, gameAnnounced
		
	soup = getGame(game)
	if soup == "404":
		return '404'

	if gameAnnounced == False:
		for i in range(0, len(channels)):
			teams = soup.find_all("span", {"class" : 'countries'})[0].string
			bot.say(channels[i], str('Game '+args+': '+teams))
			gameAnnounced = True

	if checkEndGame(soup) == True:
		line1, line2 = endGameStats(soup)
		for i in range(0, len(channels)):
			bot.say(channels[i], line1)
			bot.say(channels[i], line2)
			bot.say(channels[i], 'wm2014.py stopped on '+channels[i])
			del channels[i]
		waiter = 0
	else:
		for x in reversed(range(0, len(soup.find_all('table')))):
			for y in reversed(range(0, len(soup.find_all('table')[x].tbody.find_all('tr')))):
				status, ircoutput = parseEvent(soup.find_all('table')[x], y)
				if status != -1:
					for Channel in channels:
						bot.say(Channel, ircoutput)
		writeCache(game)

def command_score(bot, user, channel, args):
	getScores(args, bot, user, channel, args)

def command_enable(bot, user, channel, args):
	if user.split("!")[1] != 'T-101@darklite.fi': return
	if args == '':
		bot.say(channel, 'enter game number')
		return
	channels.append(channel)
	global waiter
	waiter = 1
	for i in range(0, len(channels)):
		bot.say(channels[i], "wm2014.py started on "+channels[i])
	if len(channels) == 1:
		while waiter:
			time.sleep(10)
#			bot.say(channel, "still waiting")
			command_score(bot, user, channel, args)

def command_disable(bot, user, channel, args):
	if user.split("!")[1] != 'T-101@darklite.fi': return
	for channel in channels:
		bot.say(channel, "wm2014 stopped on "+channel)
	for i in range(0, len(channels)):
		if channels[i] == channel: del channels[i]
	global waiter
	waiter = 0

def command_timerstart(bot, user, channel, args):
	if user.split("!")[1] != 'T-101@darklite.fi': return
	timerClock = 1
	bot.say(channel, 'timer started')
	while timerClock:
		timeNow = time.strftime('%d %m %Y %H %M')
		if timeNow == '20 05 2014 20 45': command_enable(bot, user, channel, '55')
		time.sleep(60)

def command_timerstop(bot, user, channel, args):
	if user.split("!")[1] != 'T-101@darklite.fi': return
	timerClock = 0
	bot.say(channel, 'timer stopped');
# WM2014.py by T-LOL