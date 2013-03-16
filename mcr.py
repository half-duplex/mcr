#!/usr/bin/env python3

# mcr.py
# This file is part of the MCR project
# Copyright 2013 Trevor Bergeron, et al., all rights reserved

import argparse
import logging
from libmcr import *

parser=argparse.ArgumentParser(
        prog="mcr", # statically set the program name shown in usage, etc
        usage="usage: mcr [args] command [data]",
        formatter_class=argparse.RawDescriptionHelpFormatter, # don't touch my line breaks
        description="Minecraft Runner (mcr), Python Edition",
        epilog='''command options:
  attach | a        attach to console (Ctrl+b d to disconnect)
  backup [remote]   back up the server [remote: to the server in cfg]
  kill              terminate the server - MAY CAUSE MAP OR DB CORRUPTION
  mkconfig          append a sample config file to ~/.config/mcr/sample
  restart           restart the server
  send message      writes "message" to the server's console
  start             starts the server
  status            checks server status (return 0: running 1: stopped)
  stop              nicely stops the server
  update [plugin]   updates or installs all or specified plugin(s)

Copyright 2013 Trevor Bergeron & Sean Buckley, all rights reserved
Please report bugs to mallegonian@gmail.com''')
parser.add_argument("command",help="what to do (see below)")
verbosity_args=parser.add_mutually_exclusive_group()
verbosity_args.add_argument("-v","--verbose",help="increase output verbosity, stacks to 2",
            action="count",default=0,dest="verbose")
verbosity_args.add_argument("-q","--quiet",help="restrict output, stacks to 2",
            action="count",default=0,dest="quiet")
parser.add_argument("data",help="any other info for the command, esp. _send_",
            nargs=argparse.REMAINDER,default="")
parser.add_argument("-V","--version",action="version",
            version="%(prog)s 0.1-dev, libmcr "+libmcr_version)
parser.add_argument("-i","--instance",help="specify a server instance",
            metavar="servername",dest="configname",default="")
cfgsource_args=parser.add_mutually_exclusive_group()
cfgsource_args.add_argument("-c","--config",help="specify an alternate config file",
            metavar="filename",dest="configfile",default="")
cfgsource_args.add_argument("-u","--user",help="specify an alternate user's config file",
            metavar="username",dest="configuser",default="")
args=parser.parse_args()
if args.quiet>=2:
    loglevel=logging.CRITICAL
elif args.quiet==1:
    loglevel=logging.ERROR
elif args.verbose==0:
    loglevel=logging.WARNING
elif args.verbose==1:
    loglevel=logging.INFO
elif args.verbose>=2:
    loglevel=logging.DEBUG
logging.basicConfig(level=loglevel)
    
logging.info("args:"+str(vars(args))) # needs logging set up already

if args.command=="mkconfig":
    with open(os.path.expanduser("~"+args.configuser)+"/.config/mcr","a") as cfgr:
        cfgr.write('''
;; Sample config
;[default] ; server instance name
;dir=/home/minecraft/minecraft ; the directory to run the server from (and to back up)
;tmuxname=mc ; the name of the tmux session
;jar=craftbukkit.jar -log-strip-color true ; the jar and arguments to run
;backupdir=/home/minecraft/minecraft-backups/ ; where to back up to for local. will create backupdir/20130223030000/
;backupremotemethod=rsync-ssh ; supported: scp, rsync-ssh
;backupremotetype=update ; update: one up-to-date backup. collect: old backups plus this one.
;backupremoteaddress=minecraft@other-host.de:/home/minecraft/minecraft-backups/
''')
        print("A sample config file has been appended to")
        print("   ",os.path.expanduser("~"+args.configuser)+"/.config/mcr")
        exit(0)

server=Server(args.configname,args.configuser,args.configfile)

if args.command=="a": args.command="attach"
if args.command in ["attach","backup","kill","restart","send","start","status","stop","update"]:
    logging.debug("Passing to Server.%s()"%(args.command))
    exit(getattr(server,args.command)())

print("Unrecognized command \"",args.command,"\"",sep="")
parser.print_help()
exit(1)

