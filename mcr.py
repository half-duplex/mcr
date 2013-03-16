#!/usr/bin/env python3

# mcr.py
# This file is part of the MCR project
# Copyright 2013 Trevor Bergeron, all rights reserved

import argparse
from libmcr import *

parser=argparse.ArgumentParser(
        description="Minecraft Runner (mcr), Python Edition",
        epilog="Copyright Trevor Bergeron 2013, bugs to mallegonian@gmail.com")
parser.add_argument("command",help="What to do")
verbosity=parser.add_mutually_exclusive_group()
verbosity.add_argument("-v",help="increase output verbosity, stackable",action="count",default=0)
verbosity.add_argument("-q",help="restrict output",action="store_true")
args=parser.parse_args()

print(args)

def printhelp(section=""):
    sections={}
    sections["usage"]="Usage: TBD"
    sections["help"]="Smartass."
    if not section in sections:
        section="usage"
    print(sections[section])

server=Server()






