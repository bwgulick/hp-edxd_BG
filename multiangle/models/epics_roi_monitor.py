# -*- coding: utf8 -*-

# DISCLAIMER
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# Principal author: R. Hrubiak (hrubiak@anl.gov)
# Copyright (C) 2018-2019 ANL, Lemont, USA


from epics import caput, caget, PV
#from epics.utils import BYTES2STR   # unused, and gone from pyepics 3.5+
import numpy as np
#from epics.clibs import *
import copy
import time
import utilities.hpMCAutilities as hpUtil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox


class epicsRoiMonitor():

    def __init__(self, record_name='16bmb:aim_adc1'):
        
        super().__init__()
        
        self.verbose = True
        self.record_name = record_name
        self.max_rois = 24      
        self.initOK = False                  
        self.mcaPV = PV(self.record_name)
        
        test = self.mcaPV.get()
        if test is not None:
            self.initOK = True
        if self.initOK:
            self.initOK = False
            
            if self.verbose:
                start_time = time.time()

            # Construct the names of the PVs for the ROIs
            self.roi_def_pvs=[]
            self.roi_data_pvs=[]
            for i in range(self.max_rois):
                n = 'R'+str(i)
                r = {n+'lo'  : None,
                    n+'hi'  : None,
                    n+'bg'  : None,
                    n+'nm'  : None}
                self.roi_def_pvs.append(r)
                r = {n       : None,
                    n+'n'   : None}
                self.roi_data_pvs.append(r)
            for roi in range(self.max_rois):
                for pv in self.roi_def_pvs[roi].keys():
                    name = self.record_name + '.' + pv.upper()
                    self.roi_def_pvs[roi][pv] = PV(name)
                for pv in self.roi_data_pvs[roi].keys():
                    name = self.record_name + '.' + pv.upper()
                    self.roi_data_pvs[roi][pv] = PV(name)


            if self.verbose:
                print("init --- %s seconds ---" % (time.time() - start_time))

            self.end_time = ''
            self.initOK = True


    def get_rois(self):
        """     Reads the ROI information from the EPICS mca record.  Stores this information
        in the epicsMca object, and returns a list of McaROI objects with this information.
        """
        if self.verbose:
            start_time = time.time()
        rois = []
        for i in range(self.max_rois):
            roi = McaROI()
            pvs = self.roi_def_pvs[i]
            r = 'R'+str(i)
            roi.left      = pvs[r+'lo'].get()
            roi.right     = pvs[r+'hi'].get()
            roi.label     = pvs[r+'nm'].get()
            #roi.bgd_width = pvs[r+'bg'].get()
            roi.use = 1
            if (roi.left > 0) and (roi.right > 0): rois.append(roi)
        self.auto_process_rois=True
        super().set_rois(rois)
        if self.verbose:
            print("get_rois --- %s seconds ---" % (time.time() - start_time))
        return self.rois