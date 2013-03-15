#!/usr/bin/python3
from libmcr import *

def printhelp(section=""):
    print("Minecraft Runner (mcr) python edition")
    print("By Trevor Bergeron, mallegonian@gmail.com")
    sections={}
    sections["usage"]="Usage: TBD"
    sections["help"]="Tehehe, smartass."
    if not section in sections:
        section="usage"
    print(sections[section])

dir(getservers())






