# libmcr.py
# This file is part of the MCR project
# Copyright 2013 Trevor Bergeron, et al., all rights reserved

import configparser
import logging
import os
import subprocess
import sys

libmcr_version="0.1-dev"

logger = logging.getLogger("libmcr")
# At the moment these cause double logging
#ch = logging.StreamHandler()
#formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s] %(message)s')
#ch.setFormatter(formatter)
#logger.addHandler(ch)


class Server(object):
    """ A minecraft server """

    def __init__(self,name=None,user=None,configfile=None):#,loglevel=logging.WARNING):
        name = name if name else "default"
        user = user if user else ""
        if configfile: # specified: check existence
            if not os.path.exists(configfile):
                configfile = os.getcwd()+configfile
                if not os.path.exists(configfile):
                    print("Could not find config file!")
        else: configfile=os.path.expanduser("~"+user)+"/.config/mcr"
        self.name=name
        self.user=user
        class MyConfigParser(configparser.ConfigParser):
            def as_dict(self):
                d = dict(self._sections)
                for k in d:
                    d[k] = dict(self._defaults, **d[k])
                    d[k].pop('__name__', None)
                return d
        mycfgp=MyConfigParser()
        mycfgp.read(configfile)
        allconfigs=mycfgp.as_dict()
        if len(allconfigs)<1:
            print("No or empty config file. See \"mcr mkconfig\" or documentation.")
            return
        if not name in allconfigs:
            print("No server section found for \"",name,"\".",sep="")
            return
        config=allconfigs[name]
        logger.info("loaded cfg:"+str(config))
        self.tmuxname = config["tmuxname"] if "tmuxname" in config and config["tmuxname"] else "mc"

    def attach(self):
        os.execlp("tmux","tmux","a","-t",self.tmuxname) # argv[0] = called name

    def backup(self):
        print("Not implemented")

    def kill(self):
        print("Not implemented")

    def restart(self):
        print("Not implemented")

    def send(self):
        print("Not implemented")

    def start(self):
        print("Not implemented")

    def status(self):
        ret=subprocess.call(["tmux","has-session","-t",self.tmuxname], stdout=open(os.devnull, 'w'),stderr=open(os.devnull, 'w'))
        if ret==0: print("running")
        else: print("stopped")
        return(ret)

    def stop(self):
        print("Not implemented")

    def update(self):
        print("Not implemented")


def getservers(user=""):
    """ Create a dictionary of all servers for a(=this) user """
    servers={}
    for svname in os.listdir(os.path.expanduser("~"+user)+"/.config/mcr/"):
        servers[svname]=Server(svname,user)
    return servers

