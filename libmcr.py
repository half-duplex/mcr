"""
libmcr.py
This file is part of the MCR project
Copyright 2013 Trevor Bergeron & Sean Buckley, all rights reserved
"""

import configparser
from datetime import datetime
import logging
import os
from shutil import copytree, ignore_patterns
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
    """ An instance of a minecraft server """

    (
        ERROR_NONE,
        ERROR_GENERAL,
        ERROR_CONFIG,
        ERROR_NOT_RUNNING,
        ERROR_NOT_IMPLEMENTED
        ) = (0,1,2,3,99)

    javacmd="java"

    def __init__(self,name=None,user=None,configfile=None):
        if not name or not isinstance(name, str): name = "default"
        if not user or not isinstance(user, str): user = ""
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
            return(self.ERROR_CONFIG)
        if not name in allconfigs:
            logger.error("No server section found for \"",name,"\"")
            return(self.ERROR_CONFIG)
        config = allconfigs[name]
        logger.info("loaded cfg ("+name+"):"+str(config))

        if "dir" in config and os.path.exists(config["dir"]):
            self.directory = config["dir"]
        else:
            logger.error("required option \"dir\" invalid or not set")
            return(self.ERROR_CONFIG)
        self.tmuxname = config["tmuxname"] if "tmuxname" \
            in config and config["tmuxname"] else "mc"
        if "jar" in config:
            self.jar = config["jar"]
        else:
            logger.error("required option \"jar\" not found in config")
            return(self.ERROR_CONFIG)
        if "backupdir" in config:
            self.backupdir = config["backupdir"]
        if "backupremotetype" in config:
            self.backupremotetype = config["backupremotetype"]
        if "backupremoteaddress" in config:
            self.backupremoteaddress = config["backupremoteaddress"]

    def attach(self):
        """ Attach to the server """
        if self.status():
            logger.error("server not running, can't attach")
            return(self.ERROR_NOT_RUNNING)
        # argv[0] is called binary name. Need os.execlp so tmux _replaces_ py.
        return(os.execlp("tmux","tmux","a","-t",self.tmuxname))

    def backup(self,remote=False):
        """ Back up the server
        remote: copy to the configured remote location after backup

        note: omits *.log
        """
        if remote:
            logger.error("Remote not implemented")
            return(self.ERROR_NOT_IMPLEMENTED)
        if len(self.backupdir)<1:
            logger.error("backup directory not set, see \"mcr mkconfig\"")
            return(self.ERROR_CONFIG)
        now = datetime.now()
        nows = "/backup_" + str(now.year) + str(now.month) + str(now.day)
        nows = nows + str(now.hour) + str(now.minute) + str(now.second) + "/"
        status = self.status()
        if status==0: # pre-notify and setup
            self.send("") # empty line
            self.send("broadcast [Backing up]")
            self.send("save-off")
            sleep(0.1) # needed?
            self.send("save-all")
        logger.debug("backing up to "+self.backupdir+nows)
        ret=0 # return status
        if not os.path.exists(self.backupdir):
            logger.error("backup directory does not exist")
            ret=self.ERROR_GENERAL
        else:
            try: copystatus = copytree(self.directory, self.backupdir+nows,
                    ignore=ignore_patterns('*.log'))
            except:
                logger.error("backup copy failed")
                ret=self.ERROR_GENERAL

        if status==0: # post-notify and cleanup - MUST BE RUN!
            self.send("") # empty line
            self.send("save-on")
            if not ret: self.send("broadcast [Backup complete]")
            else: self.send("broadcast [Backup failed, notify staff]")
        # TODO: remote
        return(ret)

    def kill(self): # TODO: make work w/ pid etc
        """ Kill the server ('s tmux session) """
        logger.warning("kill sometimes only kills the tmux session, not java!")
        return(subprocess.call(["tmux","kill-session","-t",self.tmuxname],
            stdout=open(os.devnull, 'w'),stderr=open(os.devnull, 'w')))

    def restart(self,wait=60,message=None,delay=60): # blocks until stopped!
        if self.status() == 0:
            if not message: message="Restarting server in "+delay+" seconds"
            if self.stop(wait=60,
                    message="Restarting server in "+delay+" seconds",
                    delay=delay) != 0:
                logger.error("couldn't stop server, restart failed")
                return(self.ERROR_GENERAL)
        else:
            logger.warning("server wasn't running, starting anyway")
        self.start()
        return(self.status())

    def send(self,data):
        if self.status():
            logger.error("server not running, can't send")
            return(self.ERROR_NOT_RUNNING)
        if not type(data) is str:
            data=" ".join(data)
        logger.debug("sending to "+self.tmuxname+" data: "+data)
        return(subprocess.call(["tmux","send-keys","-t",self.tmuxname+":0.0",data,"C-m"],
            stdout=open(os.devnull, 'w'),stderr=open(os.devnull, 'w')))

    def start(self):
        if self.status() == 0:
            logger.error("server already running")
            return(self.ERROR_GENERAL)
        # TODO: verify trap
        command = "trap \"\" 2 20 ; exec " + self.javacmd + " -jar " + self.jar #includes jar args
        logger.debug("command: "+command)
        subprocess.call(
            ["tmux","new-session","-ds",self.tmuxname, "sh"],
            stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        time.sleep(0.1) # prettier to not print twice waiting for sh start
        self.send("cd "+self.directory+" ; "+command)
        return(self.status())

    def status(self):
        """ Check the server's (tmux session's) status
        returns 0 for running, 1 for stopped
        """
        return(subprocess.call(["tmux","has-session","-t",self.tmuxname],
            stdout=open(os.devnull, 'w'),stderr=open(os.devnull, 'w')))

    def stop(self,wait=30,message=None,delay=10):
        """
        wait: seconds to wait until the server is stopped before timing out
        message: message to send to users
        """
        if self.status()==1:
            logger.error("server already stopped")
            return(self.ERROR_GENERAL)
        self.send("") # newline
        if message == None:
            message = "Server stopping in " + str(delay) + " seconds..."
        if len(message)>0:
            self.send("broadcast "+message)
        time.sleep(delay)
        self.send("") # newline
        #self.send("timings merged")
        self.send("save-all")
        time.sleep(3)
        self.send("stop")
        for i in range(0,wait):
            if self.status() == 0:
                return(self.ERROR_NONE)
            time.sleep(1)
        return(self.ERROR_GENERAL)

    def update(self,plugins=None):
        if not plugins: plugins = ["all"]
        logger.debug("updating plugins: "+str(plugins))
        if not os.path.exists(self.directory+"/plugins/"):
            logger.error("plugin directory does not exist")
            return(self.ERROR_GENERAL)
        pjarlist=os.listdir(self.directory+"/plugins/")
        for pjar in pjarlist:
            if pjar[-4:]==".jar":
                pset=pjar[:-4].split("_")
                pname=str(pset[0])
                if "all" in plugins or pname in plugins:
                    logger.debug("checking "+pset[0]+" "+pset[1])
                    # update
                    return(self.ERROR_NONE)
        # not already installed
        # update


def getservers(user=""):
    """ Create a dictionary of all servers for a(=this) user """
    servers = {}
    for svname in os.listdir(os.path.expanduser("~"+user)+"/.config/mcr/"):
        servers[svname] = Server(svname,user)
    return servers

