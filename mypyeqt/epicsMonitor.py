        

from epics import caput, caget, PV
#from epics.utils import BYTES2STR   # unused, and gone from pyepics 3.5+
import numpy as np
#from epics.clibs import *
import copy
import time

from PyQt5 import QtCore, QtWidgets
    

class epicsMonitor(QtCore.QObject):
    callback_triggered = QtCore.pyqtSignal(str)
    connection_callback_triggered = QtCore.pyqtSignal(bool)

    def __init__(self, pv, debounce_time=None, autostart=False):
        super().__init__()
        self.PV = pv
        self.monitor_On = False
        self.connection_monitor_On = False
        self.emitted_timestamp = None
        
        if autostart:
            self.SetPVmonitor()
            self.SetPVConnectionMonitor()
            
    def SetPVConnectionMonitor(self):
        self.PV.connection_callbacks = [self.onPVConnectionChange]
        self.connection_monitor_On = True
        
    def unSetPVConnectionmonitor(self):
        self.PV.connection_callbacks = []
        self.connection_monitor_On = False

    def SetPVmonitor(self):
        self.PV.clear_callbacks()
        self.PV.add_callback(self.onPVChange)
        self.monitor_On = True

    def unSetPVmonitor(self):
        self.PV.clear_callbacks()
        self.monitor_On = False

    def onPVChange(self, pvname=None, char_value=None, **kws):
        self.callback_triggered.emit(char_value)

    def onPVConnectionChange(self, pvname=None, conn=None, **kws):
        self.connection_callback_triggered.emit(conn)