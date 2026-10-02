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



__version__ = "0.7.3"



import argparse
import os
import sys

import PyQt5
import pyqtgraph as pg
from PyQt5 import QtCore

from PyQt5 import QtWidgets

import platform

import pathlib

desktop = pathlib.Path.home() / 'Desktop'


resources_path = os.path.join(os.path.dirname(__file__), 'resources')
calibrants_path = os.path.join(resources_path, 'calibrants')
icons_path = os.path.join(resources_path, 'icons')
data_path = os.path.join(resources_path, 'data')
style_path = os.path.join(resources_path, 'style')

file_settings_file = 'hpMCA_file_settings.json'
folder_settings_file='hpMCA_folder_settings.json'
defaults_settings_file='hpMCA_defaults.json'
file_naming_settings_file = 'hpMCA_file_naming_settings.json'

epics_sync = False

from pathlib import Path
home_path = str(Path.home())

def make_dpi_aware():
    _platform = platform.system()
    if _platform == 'Windows':
      if int(platform.release()) >= 8:
          import ctypes
          ctypes.windll.shcore.SetProcessDpiAwareness(True)

def _build_arg_parser():
    """Command-line options for launching hpMCA preloaded.

    Added so hpMCA can be started from an external controls GUI (Bluesky/BITS at
    16-BM-B) with something already open, instead of a blank window the operator
    then has to drive by hand. Bare ``python hpMCA.py`` with no options behaves
    exactly as it always has.

    Each option maps onto a controller call the author already used in the
    autoload/debug block below -- no new API.
    """
    parser = argparse.ArgumentParser(
        prog='hpMCA',
        description='hpMCA - energy dispersive XRD spectrum viewer and analysis.')
    parser.add_argument(
        '--detector', metavar='PV', default=None,
        help='EPICS mca record name to open in live view, e.g. 16bmbDante:mca1. '
             'hpMCA writes calibration, ROIs and acquisition commands to this '
             'record, so do not point it at a record another client owns.')
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        '--file', metavar='PATH', default=None,
        help='spectrum file to open in file view.')
    source.add_argument(
        '--folder', metavar='PATH', default=None,
        help='folder of spectra to open in the multi-spectra browser.')
    parser.add_argument(
        '--calibration', metavar='PATH', default=None,
        help='calibration file to load into whichever mca ends up in the foreground.')
    parser.add_argument(
        '--version', action='version', version='hpMCA ' + __version__)
    return parser


def _autoload(controller, options):
    """Apply the parsed command-line options to a constructed controller.

    Order matters: the detector is opened first, then a file or folder, so that
    giving both leaves the file data in the foreground (the more specific
    request wins). The calibration is applied last, to whatever is foreground.

    A bad path is reported on stderr and skipped rather than raised -- the GUI
    is already up by this point, and a launcher passing a stale path should get
    a usable window plus a complaint, not a traceback and no window.
    """
    if options.detector:
        controller.openDetector(detector=options.detector)

    if options.file:
        if os.path.isfile(options.file):
            controller.file_save_controller.openFile(filename=options.file)
        else:
            print('hpMCA: --file not found: %s' % options.file, file=sys.stderr)

    if options.folder:
        if os.path.isdir(options.folder):
            controller.file_save_controller.openFolder(foldername=options.folder)
        else:
            print('hpMCA: --folder not found: %s' % options.folder, file=sys.stderr)

    if options.calibration:
        if os.path.isfile(options.calibration):
            controller.load_calibration(filename=options.calibration)
        else:
            print('hpMCA: --calibration not found: %s' % options.calibration,
                  file=sys.stderr)


def main(argv=None):

    options = _build_arg_parser().parse_args(sys.argv[1:] if argv is None else argv)

    make_dpi_aware()
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
      PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
   
    app = QtWidgets.QApplication([])

    from hpm.controllers.hpmca_controller import hpmcaController
    app.aboutToQuit.connect(app.deleteLater)

    # autoload a file, using for debugging
    #pattern = os.path.normpath(os.path.join(resources_path,'20181010-Au-wire-50um-15deg.hpmca'))
    #pattern2 = os.path.normpath(os.path.join(resources_path,'20181001 Energy Calibration.000'))
    #jcpds1 = os.path.normpath(os.path.join(resources_path,'au.jcpds'))
    #jcpds2 = os.path.normpath(os.path.join(resources_path,'mgo.jcpds'))
    #multi_spectra =  os.path.normpath( os.path.join(desktop,'dt/Guoyin/Cell2-HT/5000psi-800C'))
    #multi_spectra2 =  os.path.normpath( os.path.join(desktop,'dt/20221213-SiO2'))
    #multi_spectra3 =  os.path.normpath( os.path.join(desktop,'dt/20230219_Fe/xrd/tth-scan'))
    #multi_spectra4 =  os.path.normpath( os.path.join(desktop,'dt/20230406_SiO2/0psi'))
    #mask_path =  os.path.normpath( os.path.join(resources_path,'my.mask'))
    #multi_element =  os.path.normpath( os.path.join(resources_path,'basalt_xrf.002'))
    
    #multi_element_calibration =  os.path.normpath( os.path.join(desktop,'dt/GSD/20221203_Cd109-Co57_5400sec_gain100kev_summed.hpmca'))
    #multi_element = os.path.normpath( os.path.join(desktop, 'dt/GSD/sio2/20221204_Au_60sec_filter-glassy-C_beam-0p05x0p05_angle-2_003.dat.mca'))
    #multi_element =  os.path.normpath( os.path.join(resources_path,'20221116_test_010.hpmca'))
    #pattern = os.path.join(resources_path,'LaB6_40keV_MarCCD.chi')
    #jcpds = os.path.join(resources_path,'LaB6.jcpds')

    controller = hpmcaController(app)
    controller.widget.show()

    #controller.file_save_controller.openFile(filename=multi_element)
    #controller.load_calibration(filename=multi_element_calibration)
    #controller.file_save_controller.openFolder(foldername=multi_spectra4)
    #controller.element_number_cmb_currentIndexChanged_callback(1)
    
    #controller.file_save_controller.openFolder(foldername=multi_spectra2)
    #controller.multiple_datasets_controller.mask_controller.load_mask_btn_click(filename = mask_path)
    #controller.multiple_datasets_controller.show_view()
    
    #controller.phase_controller.add_btn_click_callback(filenames=[jcpds1])

    #controller.phase_controller.show_view()
    #controller.phase_controller.add_btn_click_callback(filenames=['JCPDS/Oxides/mgo.jcpds'])

    _autoload(controller, options)

    return app.exec_()


