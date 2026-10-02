
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



from epics import caput, caget, PV
#from epics.utils import BYTES2STR   # unused, and gone from pyepics 3.5+
import numpy as np
#from epics.clibs import *
import copy
import time

from PyQt5 import QtCore, QtWidgets
from mypyeqt.CustomWidgets import HorizontalSpacerItem
import pyqtgraph as pg

from mypyeqt.pvWidgets import pvQDoubleSpinBox, pvQOZButton, pvQCheckBox, \
                                pvQMessageButton, pvQLineEdit, pvQLabel, pvStripChart


class stripChart(QtCore.QObject):
   
    def __init__(self, app):
        super().__init__()
   

        pvs = ['16bmb:DMM1Ch9_calc.VAL', '16bmb:DMM1Ch10_calc.VAL','16bmb:PS66xxA:PS1:SR:powerOutPut']

        self.widget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        
        self.pv_lbls = []
        for pv in pvs:

            pv_widget = QtWidgets.QHBoxLayout()
            pv_widget.addWidget(QtWidgets.QLabel(pv))
            lbl = pvQLabel(pv)
            pv_widget.addWidget(lbl)
            pv_widget.addSpacerItem(HorizontalSpacerItem())
            
            self.pv_lbls.append(lbl)
            self._layout.addLayout(pv_widget)

        self.strip_chart_widget = stripChartWidget(pvs)
        self._layout.addWidget(self.strip_chart_widget)
      
        self.widget.setLayout(self._layout)


        self.widget.show()

   ############################################################################


class stripChartWidget(QtWidgets.QWidget):
    def __init__(self, pvs):
        super().__init__()

        self._layout = QtWidgets.QGridLayout()

        self.plot1 = pvStripChart(pvs[0])
        self.plot2 = pvStripChart(pvs[1])
        self.plot3 = pvStripChart(pvs[2])
        #self.plot4 = pvStripChart(pvs[3])
        self._layout.addWidget(self.plot1,0,0)
        self._layout.addWidget(self.plot2,1,0)
        self._layout.addWidget(self.plot3,0,1)
        #self._layout.addWidget(self.plot4,1,1)
        self.setLayout(self._layout)