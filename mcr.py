#!/usr/bin/env python3

# mcr.py
# This file is part of the MCR project
# Copyright 2013 Trevor Bergeron, et al., all rights reserved

import argparse
from libmcr import *

parser=argparse.ArgumentParser(
        prog="mcr", # statically set the program name shown in usage
        formatter_class=argparse.RawDescriptionHelpFormatter, # don't touch my line breaks
        description="Minecraft Runner (mcr), Python Edition",
        epilog='''command options:
  attach | a        attach to console (Ctrl+b d to disconnect)
  backup [remote]   back up the server [remote: to the server in cfg]
  kill              terminate the server - MAY CAUSE MAP OR DB CORRUPTION
  mkconfig          write a sample config file to ~/.config/mcr/sample
  restart           restart the server
  send message      writes "message" to the server's console
  start             starts the server
  status            checks server status (return 0: running 1: stopped)
  stop              nicely stops the server

Copyright 2013 Trevor Bergeron & Sean Buckley, all rights reserved
Please report bugs to mallegonian@gmail.com''')
parser.add_argument("command",help="what to do")
verbosity_args=parser.add_mutually_exclusive_group()
verbosity_args.add_argument("-v","--verbose",help="increase output verbosity, stackable",action="count",default=0)
verbosity_args.add_argument("-q","--quiet",help="restrict output",action="store_true") # default=False
parser.add_argument("data",help="any other info for the command, esp. _send_",nargs=argparse.REMAINDER,default="")
parser.add_argument("-V","--version",action="version",version="%(prog)s 0.1-dev, libmcr "+libmcr_version)
parser.add_argument("-c","--config",help="specify an alternate config file")
args=parser.parse_args()

# parse ["a","attach","backup","kill","mkconfig","restart","send","start","status","stop"]


print(args)

def printhelp(section=""):
    sections={}
    sections["usage"]="Usage: TBD"
    sections["help"]="Smartass."
    if not section in sections:
        section="usage"
    print(sections[section])

server=Server()






