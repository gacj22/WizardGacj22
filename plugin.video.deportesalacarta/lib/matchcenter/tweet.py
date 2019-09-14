# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------

import re
import datetime
import time
import xbmcgui
import xbmc
from core import jsontools
from twitter import *

from core import filetools
from core import config

con_secret='h7hSFO1BNKzyB2EabYf7RXXd5'
con_secret_key='tVbNWktkILCHu9CcENhXaUnLOrZWhJIHvBNcSEwgaczR8adZwU'
token='1226187432-3Tn0Euwt604LvNXGsVYWrgBrXa2xboo3UFgbrha'
token_key='KccVJ7kUFJhG7uZgJeQNizEbf9Z9spZDhEKGP3b3ogrH2'

twitter_history_file = filetools.join(config.get_data_path(), 'matchcenter', "twitter_history.txt")

t = Twitter(
    auth=OAuth(token, token_key, con_secret, con_secret_key))


def get_tweets(twitter_user,twitter_hash,twitter_search,go_tweet, max_id="", filtro_rt=""):
    return_twitter = []
    total = None

    tipos = ["mixed", "recent", "popular"]
    tipo = tipos[int(config.get_setting("type_tweets"))]
    filtro_lang = ""
    if int(config.get_setting("lang_tweets")) == 1:
        filtro_lang = "es"

    if twitter_hash:
        if twitter_hash == "notuser":
            return_twitter = None
            return return_twitter
        twitter_hash = twitter_hash.replace("#", "")
        if max_id:
            tweet_list = t.search.tweets(q=twitter_hash, count=20, max_id=max_id, tweet_mode="extended", lang=filtro_lang, exclude=filtro_rt, result_type=tipo)['statuses']
        else:
            tweet_list = t.search.tweets(q=twitter_hash, count=20, tweet_mode="extended", lang=filtro_lang, exclude=filtro_rt, result_type=tipo)['statuses']
    elif twitter_user:
        twitter_user = twitter_user.replace("@", "")
        if max_id:
            tweet_list = t.statuses.user_timeline(screen_name=twitter_user, count=20, max_id=max_id, tweet_mode="extended")
        else:
            tweet_list = t.statuses.user_timeline(screen_name=twitter_user, count=20, tweet_mode="extended")
        total = 0
    elif go_tweet:
        total = 0
        ok_reply = t.statuses.show(id=go_tweet, tweet_mode="extended")
        tweet_list = []
        tweet_list.append(ok_reply)
    else:
        if max_id:
            tweet_list = t.search.tweets(q=twitter_search, count=20, max_id=max_id, tweet_mode="extended", lang=filtro_lang, exclude=filtro_rt, result_type=tipo)['statuses']
        else:
            tweet_list = t.search.tweets(q=twitter_search, count=20, tweet_mode="extended", lang=filtro_lang, exclude=filtro_rt, result_type=tipo)['statuses']

    if "Not authorized" in str(tweet_list):
        return "No autorizado", total

    for tweet in tweet_list:
        minm_text = None
        minm_name = None
        minm_profilepic = None
        get_reply = None
        thumb=None
        #1 vemos si es una respuesta
        reply = tweet['in_reply_to_status_id']
        try:
            if reply:
                get_reply = reply
                get_tweet = t.statuses.show(id=reply)
                try:
                    text_toreply = get_tweet['full_text'].encode("utf-8")
                except:
                    text_toreply = get_tweet['text'].encode("utf-8")
                profilepic_toreply = get_tweet['user']['profile_image_url'].replace('_normal','')
                name_toreply = get_tweet ['user']['screen_name'].encode("utf-8")
                replieded_reply = get_tweet ['in_reply_to_status_id_str']
                if replieded_reply:
                    try: 
                        get_tweet_replieded = t.statuses.show(id=replieded_reply)
                        replieded_text = get_tweet_replieded['full_text'].encode("utf-8","ignore")
                    except:
                        pass
            else:
                text_toreply = None
                profilepic_toreply = None
                name_toreply = None
                get_tweet_replieded = None
        except:
            text_toreply = None
            profilepic_toreply = None
            name_toreply = None
            get_tweet_replieded= None
        #2 buscamos  los enlaces a noticias con url acortada(Twittercards)
        twittercards_links = tweet['entities']['urls']
        if twittercards_links:
            for details in twittercards_links:
                twittercl = details["expanded_url"].encode("utf-8")
        else:
            twittercl = ""

       #3 datos del autor del tweet retweeteado
        try:
            banner_rt = tweet['retweeted_status']['user']['profile_banner_url']
        except:   
            banner_rt = None
        try:   
            profilepic_rt = tweet['retweeted_status']['user']['profile_image_url']
        except:
            profilepic_rt = None
        try:   
            name_rt = tweet['retweeted_status']['user']['screen_name'].encode("utf-8")
        except:
            name_rt = None
        try:
            text_rt = tweet['retweeted_status']['full_text']
        except:
            text_rt = None

        #4 Retweets y Favoritos del RT
        try:
            rt_rt = tweet['retweeted_status']['retweet_count']
        except:
            rt_rt = None
        try:
            fav_rt = tweet['retweeted_status']['favorite_count']
        except:
            fav_rt = None

        #imagenes e información de RT
        try:   
            url = tweet['retweeted_status']['entities']['urls']
            if url:
                for details in url:
                    url = details["expanded_url"]
            else:
                try: 
                    video_imagert = tweet['retweeted_status']['entities']['media']
                    for details in video_imagert:
                        video_imagert = details['expanded_url']
                        url = video_imagert
                except:
                    url = None
        except:
            try: 
                video_imagert = tweet['retweeted_status']['entities']['media']
                for details in video_imagert:
                    video_imagert = details['expanded_url']
                    url = video_imagert
            except:
                url = None

        reply_rt = None
        #6 Mención en RT y datos mencionado
        try:
            profilepic_rtr = tweet['retweeted_status']['quoted_status']['user']['profile_image_url_https']
            profilepic_rtr = profilepic_rtr.replace('_normal','')
            try:
                mention_inrt = tweet['retweeted_status']['quoted_status']['full_text'].encode("utf-8")
                profilepic_rtr = None
            except:
                mention_inrt = None
        except:
            profilepic_rtr = None
            mention_inrt = None

        if mention_inrt:
            mention_text = mention_inrt
            mention_name = tweet['retweeted_status']['quoted_status']['user']['screen_name'].encode("utf-8")
            mention_profilepic = tweet['retweeted_status']['quoted_status']['user']['profile_image_url_https']
            mention_profilepic = mention_profilepic.replace('_normal', '')
            mention_rt = tweet['retweeted_status']['quoted_status']['retweet_count']
            mention_fav = tweet['retweeted_status']['quoted_status']['favorite_count']
            try:
                mention_banner = tweet['retweeted_status']['quoted_status']['user']['profile_banner_url']
            except:
                mention_banner = "http://imgur.com/7a5rIDJ.jpg"
            try:
                mention_url = tweet['retweeted_status']['quoted_status']['entities']['urls']
                if str(mention_url) == "[]":       
                    mention_url = tweet['retweeted_status']['quoted_status']['entities']['media']
                    for details in mention_url:
                        mention_url = details['media_url_https']
                else:
                    for details in mention_url:
                        mention_url = details['url']
            except:
                mention_url = None
        else:
            try:
                mention_text = tweet['quoted_status']['full_text'].encode("utf-8")
            except:
                mention_text = None
            try:   
                mention_name = tweet['quoted_status']['user']['screen_name'].encode("utf-8")
                mention_profilepic = tweet['quoted_status']['user']['profile_image_url_https']
                mention_profilepic = mention_profilepic.replace('_normal', '')
                mention_rt = tweet['quoted_status']['retweet_count']
                mention_fav = tweet['quoted_status']['favorite_count']
            except:
                mention_name = None 
                mention_profilepic = None
                mention_rt = None
                mention_fav = None

            try:
                mention_banner = tweet['quoted_status']['user']['profile_banner_url']
            except:
                mention_banner = "http://imgur.com/7a5rIDJ.jpg"
            try:
                mention_url = tweet['quoted_status']['entities']['urls']
                if str(mention_url) == "[]":       
                    mention_url = tweet['quoted_status']['entities']['media']
                    for details in mention_url:
                        mention_url = details['media_url_https']
                else:
                    for details in mention_url:
                        mention_url = details['url']
            except:
                mention_url = None

        if twitter_user:
            if re.search(r'(?i)%s' % twitter_user, tweet['user']['screen_name']) and total == 0:
                total = int(tweet['user']['statuses_count'])
        tweet['created_at'] = tweet['created_at'].replace(" +0000","")
        tweet['date'] = datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S %Y")))  - datetime.timedelta(seconds=15)
        #Videos e imagenes
        images = []
        videos = []
        for media in tweet.get("extended_entities", {}).get("media", []):
            if media.get('video_info'):
                for i, video in enumerate(media["video_info"]["variants"]):
                    if video['content_type'] == 'video/mp4':
                        videos.append({"url":video['url'], "bitrate":video["bitrate"]})
                videos.sort(key=lambda v:v.get("bitrate", ""), reverse=True)
                if media.get('media_url_https'):
                    thumb = media.get('media_url_https')
            else:
                images.append(media["media_url"])

        #Se busca videos e imagenes en RT ,en su defecto,menciones en menciones
        if str(images) == "[]" and str(videos) == "[]":
            try:
                check_rtm = tweet['retweeted_status']
            except:
                check_rtm = None

            if check_rtm:
                for media in tweet.get("retweeted_status").get("extended_entities", {}).get("media", []):
                    if media.get('video_info'):
                        for i, video in enumerate(media["video_info"]["variants"]):
                            if video['content_type'] == 'video/mp4':
                                videos.append({"url":video['url'], "bitrate":video["bitrate"]})
                        videos.sort(key=lambda v:v.get("bitrate", ""), reverse=True)
                        if media.get('media_url_https'):
                            thumb = media.get('media_url_https')
                    else:
                        images.append(media["media_url"])
            check_qt = None
            if str(images) == "[]" and str(videos) == "[]":
                try:
                    check_qt = tweet['quoted_status']
                except:
                    check_qt = None

            if check_qt: 
                for media in tweet.get("quoted_status").get("extended_entities", {}).get("media", []):
                    if media.get('video_info'):
                        for i, video in enumerate(media["video_info"]["variants"]):
                            if video['content_type'] == 'video/mp4':
                                videos.append({"url":video['url'], "bitrate":video["bitrate"]})
                        videos.sort(key=lambda v:v.get("bitrate", ""), reverse=True)
                        if media.get('media_url_https'):
                            thumb= media.get('media_url_https')
                    else:
                        images.append(media["media_url"])
                if str(images) == "[]" and str(videos) == "[]":
                    try:
                        mention_in_mention = tweet['quoted_status']['quoted_status_id']
                    except:
                        mention_in_mention = None
                    if mention_in_mention:
                        get_minm = t.statuses.show(id=mention_in_mention)
                        minm_text = get_minm['text']
                        minm_name = get_minm['user']['screen_name']
                        minm_profilepic = get_minm['user']['profile_image_url_https'].replace('_normal', '')
            else:
                try:
                    check_rtq = tweet['retweeted_status']['quoted_status']
                except:
                    check_rtq = None
                if check_rtq:
                    for media in tweet.get("retweeted_status").get("quoted_status",{}).get("extended_entities", {}).get("media", []):
                        if media.get('video_info'):
                            for i, video in enumerate(media["video_info"]["variants"]):
                                if video['content_type'] == 'video/mp4':
                                    videos.append({"url":video['url'], "bitrate":video["bitrate"]})
                            videos.sort(key=lambda v:v.get("bitrate", ""), reverse=True)
                            if media.get('media_url_https'):
                                thumb= media.get('media_url_https')
                        else:
                            images.append(media["media_url"])
                    try:
                        mention_in_mention = tweet['retweeted_status']['quoted_status']['quoted_status_id']
                    except:
                        mention_in_mention = None  
                    if mention_in_mention:
                        get_minm = t.statuses.show(id=mention_in_mention)
                        minm_text = get_minm['text']
                        minm_name = get_minm['user']['screen_name']
                        minm_profilepic = get_minm['user']['profile_image_url_https'].replace('_normal', '')

        if tweet.get('retweeted_status'):
            text = "RT @%s: %s" % (tweet['retweeted_status']['user']['screen_name'],
                                   tweet['retweeted_status']['full_text'])
        else:
            try:
                text = tweet["full_text"]
            except:
                text = tweet["text"] 
        emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
        "+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        return_twitter.append({"author_rn":tweet['user']['name'],"author":tweet['user']['screen_name'], "phrase":tweet['user']['description'],
                               "profilepic":tweet['user']['profile_image_url_https'].replace('_normal',''),
                               "text":text, "date":tweet['date'], "id":tweet['id_str'], 
                               "rt":str(tweet['retweet_count']), "fav":str(tweet['favorite_count']),
                               "images":images, "videos":videos, "banner":tweet.get('user', {}).get('profile_banner_url', ''),
                               "profilepic_rt":profilepic_rt, "banner_rt":banner_rt, "":banner_rt, "url":url,
                               "reply_rt":reply_rt, "profilepic_rtr":profilepic_rtr, "twittercl":twittercl,
                               "text_toreply":text_toreply, "profilepic_toreply":profilepic_toreply,
                               "mention_text":mention_text, "mention_profilepic":mention_profilepic,
                               "mention_url":mention_url, "mention_banner":mention_banner, "rt_rt":str(rt_rt),
                               "fav_rt":str(fav_rt), "mention_rt":mention_rt, "mention_fav":mention_fav,
                               "mention_name":mention_name, "name_toreply":name_toreply, "name_rt":name_rt,
                              "text_rt":text_rt, "minm_text":minm_text, "minm_name":minm_name, "minm_profilepic":minm_profilepic,"followers":tweet['user']['followers_count'],"friends":tweet['user']['friends_count'],"location":tweet['user']['location'],"go_tweet":get_reply,"thumb":thumb})

    if twitter_user:
        return return_twitter, total
    else:
        if str(return_twitter) == "[]":
            return_twitter = None   
        return return_twitter


def user_search(twitter_usersearch, max_id=""):
    return_twitter =[]
    if max_id:
        tweet_list = t.users.search(q=twitter_usersearch,count=20, max_id=max_id)
    else:
        tweet_list = t.users.search(q=twitter_usersearch,count=20)
    
    for tweet in tweet_list:
        return_twitter.append({"name":tweet['name'], "screen_name":tweet['screen_name'],
                               "profilepic":tweet['profile_image_url_https'].replace('_normal',''),
                               "id":tweet['id_str']})
    return return_twitter


def get_twitter_history():
    twitter_history = []
    if filetools.exists(twitter_history_file):
        twitter_history = filetools.read(twitter_history_file)
        twitter_history = [hashtag for hashtag in twitter_history.split('||') if hashtag]
    return twitter_history


def savecurrenthash(_hash, file):
    if " OR " in _hash:
        _hash = _hash.split(" OR ", 1)[0]

    _hash = unicode(_hash, "utf-8", errors="replace").encode("utf-8")
    media_dict = {"hash": _hash}

    if not filetools.exists(file):
        if not filetools.exists(filetools.join(config.get_data_path(), 'matchcenter')):
            filetools.mkdir(filetools.join(config.get_data_path(), 'matchcenter'))
    filetools.write(file, jsontools.dump_json(media_dict))
    return


def add_hashtag_to_twitter_history(hashtag, search):
    history = get_twitter_history()
    import unicodedata
    if " OR " in hashtag:
        hashtag = hashtag.split(" OR ", 1)[0]

    hashtag = unicode(hashtag, "utf-8", errors="replace").encode("utf-8")+"|"+search
    if hashtag in history:
        history.remove(hashtag)

    history.append(hashtag)
    return filetools.write(twitter_history_file,"||".join(history))


def remove_twitter_hashtag_history():
    if filetools.exists(twitter_history_file):
        filetools.remove(twitter_history_file)
        xbmc.executebuiltin("XBMC.Notification(%s,%s,3000,%s)" % ("Match Center","Se ha eliminado la caché",filetools.join(config.get_runtime_path(),"icon.png")))      
    else:
        xbmcgui.Dialog().ok("Match Center", "No hay historial de Twitter disponible")


def get_trends():
    return_twitter = []
    trends = t.trends.place(_id="23424950")[0]['trends']
    for hash in trends:
        return_twitter.append(hash['name'])
    return return_twitter
