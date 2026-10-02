
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
from mypyeqt.pvWidgets import pvQDoubleSpinBox, pvQOZButton, pvQCheckBox, \
                                pvQMessageButton, pvQLineEdit, pvQLabel


class epicsPYQT(QtCore.QObject):
   
    def __init__(self, app):
        super().__init__()
   
        pv_freq_name = 'myIOC:Frequency'
        pv_btn_name = 'ScopeTrig'
        pv_cb_name = 'McaTrig'
        pv_edit_name = 'myIOC:Filename'

        bmb_test_string = '16bmb:userTran8.CMTB'
        bmb_test_float = '16bmb:userTran8.B'


        self.widget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout()
        
        
        self.freq = pvQDoubleSpinBox(bmb_test_float)
        #self.btn = pvQOZButton(pv_btn_name)
        #self.cb = pvQCheckBox(pv_cb_name)
        self.edit = pvQLineEdit(bmb_test_string)
        self.lbl = pvQLabel(bmb_test_string)

        #self.oz1 = pvQMessageButton(pv_btn_name, '1')
        #self.oz0 = pvQMessageButton(pv_btn_name, '0')
        self.oz2 = pvQMessageButton(bmb_test_float, '60')
        self.oz3 = pvQMessageButton(bmb_test_float, '100')

        self.ctrlBtn = QtWidgets.QPushButton("CONN")
        self.ctrlBtn.setCheckable(True)
        self.ctrlBtn.setChecked(True)



        #self.btn.setText("0<->1")
        #self.cb.setText("Run")

        self._layout.addWidget(self.freq)
        #self._layout.addWidget(self.btn)
        #self._layout.addWidget(self.cb)
        #self._layout.addWidget(self.oz0)
        #self._layout.addWidget(self.oz1)
        self._layout.addWidget(self.oz2)
        self._layout.addWidget(self.oz3)
        self._layout.addWidget(self.edit)
        self._layout.addWidget(self.lbl)
        self._layout.addWidget(self.ctrlBtn)

        self.widget.setLayout(self._layout)

        self.make_connections()
        self.widget.show()

    def make_connections(self):
        self.ctrlBtn.clicked.connect(self.ctrl_clicked)

    def ctrl_clicked(self):
        conn  = self.ctrlBtn.isChecked()
        if conn:
            self.freq.connect()
        else:
            self.freq.disconnect()

    def unload(self):
        
        self.live_time_preset_monitor.unSetPVmonitor()
        


    def handle_mca_callback_pltm(self, Status):
        print('handle_mca_callback_pltm: ' + str(Status))
        pass


   
   ############################################################################

