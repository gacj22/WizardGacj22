import json
import urllib
import urllib2
import team as _team
import xbmc
import datetime as _datetime


__author__ = 'enen92'
API_BASE_URL = 'http://www.thesportsdb.com/api/v1/json'

class Api:

    def __init__(self,key=None):
        global API_KEY
        API_KEY = key
        if API_KEY != None and type(API_KEY) == str:
            xbmc.log(msg="[TheSportsDB] Module initiated with API key " + str(API_KEY), level=xbmc.LOGNOTICE)
        else:
            xbmc.log(msg="[TheSportsDB] API Key is not valid", level=xbmc.LOGERROR)

    class Lookups:

        def Team(self,teamid=None,leagueid=None):
            teamlist = []
            if teamid or leagueid:
                if teamid and not leagueid:
                    url = '%s/%s/lookupteam.php?id=%s' % (API_BASE_URL,API_KEY,str(teamid))
                elif leagueid and not teamid:
                    url = '%s/%s/lookup_all_teams.php?id=%s' % (API_BASE_URL,API_KEY,str(leagueid))
                else:
                    xbmc.log(msg="[TheSportsDB] Invalid parameters", level=xbmc.LOGERROR)
                    return teamlist
                data = json.load(urllib2.urlopen(url))
                teams = data["teams"]
                if teams:
                    for tm in teams:
                        teamlist.append(_team.as_team(tm))
            else:
                xbmc.log(msg="[TheSportsDB] teamid or leagueid must be provided", level=xbmc.LOGERROR)
            return teamlist


    class Search:

        def Teams(self,team=None,sport=None,country=None,league=None):
            teamlist = []
            if team or sport or country or league:
                if team and not sport and not country and not league:
                   url = '%s/%s/searchteams.php?t=%s' % (API_BASE_URL,API_KEY,urllib.quote(team))
                elif not team and league and not sport and not country:
                    url = '%s/%s/search_all_teams.php?l=%s' % (API_BASE_URL,API_KEY,urllib.quote(league))
                elif not team and not league and sport and country:
                    url = '%s/%s/search_all_teams.php?s=%s&c=%s' % (API_BASE_URL,API_KEY,urllib.quote(sport),urllib.quote(country))
                else:
                    url = None
                if url:
                    data = json.load(urllib2.urlopen(url))
                    teams = data["teams"]
                    if teams:
                        for tm in teams:
                            teamlist.append(_team.as_team(tm))
                else:
                    xbmc.log(msg="[TheSportsDB] Invalid Parameters", level=xbmc.LOGERROR)
            else:
                xbmc.log(msg="[TheSportsDB] team,sport,country or league must be provided", level=xbmc.LOGERROR)
            return teamlist


    class Image:

        def Preview(self,image):
            if (image.startswith("http://www.thesportsdb.com/images/") and image.endswith(".png")) or (image.startswith("http://www.thesportsdb.com/images/") and image.endswith(".jpg")):
                return image + "/preview"
            else:
                return None

        def Original(self,image):
            if (image.startswith("http://www.thesportsdb.com/images/") and image.endswith(".png")) or (image.startswith("http://www.thesportsdb.com/images/") and image.endswith(".jpg")):
                return image
            else:
                return None
