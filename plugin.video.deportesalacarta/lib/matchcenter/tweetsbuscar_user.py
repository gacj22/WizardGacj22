# -*- coding: utf-8 -*-
#------------------------------------------------------------
# deportesalacarta - XBMC Plugin
#------------------------------------------------------------


ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10

import xbmcgui
from core import config
from core import filetools

import xbmc
import tweets
import tweet


class Select(xbmcgui.WindowXMLDialog):
    def __init__(self,*args, **kwargs):
        self.hash = kwargs.get("user")

    def onInit(self):
        try:
            self.control_list = self.getControl(6)
            self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
            self.getControl(3).setEnabled(0)
            self.getControl(3).setVisible(0)
        except:
            pass
        self.getControl(1).setLabel("[COLOR cadetblue][B]Elige usuario[/B][/COLOR]")
        self.getControl(5).setLabel("[COLOR red][B]Cerrar[/B][/COLOR]")
        self.control_list.reset()
        items = []
        try:
            users = tweet.user_search(self.hash) 
        except:
            users = None 
        if str(users) == "[]":
            self.close()
            tweets.start("persona", "''")
        if users:
            for user in users:
                name = user["name"].encode("utf-8","ignore")	
                name = "[COLOR bisque]"+name+"[/COLOR]"
                sc_name = user["screen_name"].encode("utf-8","ignore")
                sc_namec = "[COLOR skyblue]"+sc_name+"[/COLOR]"
                pic = user["profilepic"]
                item = xbmcgui.ListItem(name + " ("+"[COLOR gold] @[/COLOR]"+sc_namec+")")
                try:
                    item.setArt({"thumb":pic})
                except:
                    item.setThumbnailImage(pic)
                item.setProperty("sc_name", sc_name)
                items.append(item)      
        self.getControl(6).addItems(items)
        self.setFocusId(6)
  

    def onAction(self, action):
        if (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == 6:
            self.close()
            selectitem = self.getControl(6).getSelectedItem()
            sc_name = selectitem.getProperty("sc_name")
            tweets.start("persona", sc_name)
           
        elif (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == 5:
            self.close() 

        elif action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.close()

def start(twitterbuscar_user=None, standalone=False):
    dialog = xbmcgui.Dialog()
    twitterbuscar_user = dialog.input("Introduce la busqueda", type=xbmcgui.INPUT_ALPHANUM)
    if len(twitterbuscar_user) != 0:
        twitterbuscar_user = twitterbuscar_user.replace("#","")
    else:
        tweets.start("persona", "notuser")

    if twitterbuscar_user:
        select=Select('DialogSelect.xml', config.get_runtime_path(), user=twitterbuscar_user)
        select.doModal()
