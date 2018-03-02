import os, sys, inspect

#Include this smoothstreams folder in sys.path so included libs will import properly
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

from player import ChannelPlayer #analysis:ignore
from schedule import Schedule #analysis:ignore