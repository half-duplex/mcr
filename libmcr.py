"""
libmcr.py
This file is part of the MCR project
Copyright 2013 Trevor Bergeron & Sean Buckley, all rights reserved
"""

import configparser
import logging
import os
import subprocess
import sys
import time

libmcr_version = "0.1-dev"

logger = logging.getLogger("libmcr")
# At the moment these cause double logging
#ch = logging.StreamHandler()
#formatter = logging.Formatter(
#    '%(asctime)s %(name)s [%(levelname)s] %(message)s')
#ch.setFormatter(formatter)
#logger.addHandler(ch)


class Server(object):
    """ A minecraft server """

    def __init__(self,name=None,user=None,configfile=None):
        name = name if name else "default"
        user = user if user else ""
        if configfile: # specified: check existence
            if not os.path.exists(configfile):
                configfile = os.getcwd()+configfile
                if not os.path.exists(configfile):
                    print("Could not find config file!")
        else: configfile = os.path.expanduser("~"+user)+"/.config/mcr"
        self.name = name
        self.user = user
        class MyConfigParser(configparser.ConfigParser):
            def as_dict(self):
                d = dict(self._sections)
                for k in d:
                    d[k] = dict(self._defaults, **d[k])
                    d[k].pop('__name__', None)
                return d
        mycfgp = MyConfigParser()
        mycfgp.read(configfile)
        allconfigs = mycfgp.as_dict()
        if len(allconfigs)<1:
            logger.error("No or empty config file, see \"mcr mkconfig\"")
            return
        if not name in allconfigs:
            logger.error("No server section found for \"",name,"\"")
            return
        config = allconfigs[name]
        logger.info("loaded cfg:"+str(config))
        self.tmuxname = config["tmuxname"] if "tmuxname" \
            in config and config["tmuxname"] else "mc"

    def attach(self):
        if self.status():
            logger.error("server not running, can't attach")
            return
        # argv[0] is called binary name. Need os.execlp so tmux _replaces_ py.
        return(os.execlp("tmux","tmux","a","-t",self.tmuxname))

    def backup(self,remote=False):
        print("Not implemented")

    def kill(self):
        print("Not implemented")

    def restart(self):
        if self.status() == 0:
            self.stop()
        else:
            logger.warning("server wasn't running, starting anyway")
        self.start()
        return(self.status())

    def send(self):
        print("Not implemented")

    def start(self):
        print("Not implemented")

    def status(self): # 0=running, 1=stopped
        return(subprocess.call(["tmux","has-session","-t",self.tmuxname],
            stdout=open(os.devnull, 'w'),stderr=open(os.devnull, 'w')))

    def stop(self,wait=30):
        """
        wait: seconds to wait until the server is stopped before timing out
        """
        self.send("") # newline
        self.send("save-all")
        time.sleep(3)
        self.send("stop")
        for i in range(0,wait):
            if self.status() == 0:
                return(0)
            time.sleep(1)
        return(1)

    def update(self):
        print("Not implemented")


def getservers(user=""):
    """ Create a dictionary of all servers for a(=this) user """
    servers = {}
    for svname in os.listdir(os.path.expanduser("~"+user)+"/.config/mcr/"):
        servers[svname] = Server(svname,user)
    return servers

