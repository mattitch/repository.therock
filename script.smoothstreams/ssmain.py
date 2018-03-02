# -*- coding: utf-8 -*-

from lib import epg

def main():
    if epg.versionCheck(): return
    epg.ViewManager()