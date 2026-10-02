"""Throwaway: walk hpMCA's startup import chain one step at a time.

Each line is flushed before the import runs, so if the interpreter dies with an
access violation the last line printed names the import that killed it.
"""
import sys

STEPS = [
    'import numpy',
    'import epics',
    'from epics.clibs import *',
    'import PyQt5.QtWidgets',
    'import pyqtgraph',
    'import burnman',
    'from burnman.eos.equation_of_state import EquationOfState',
    'import hpm.models.jcpds',
    'import hpm.widgets.TthCalWidget',
    'import hpm.models.MaskModel',
    'import hpm.models.calcMCA',
    'from hpm.controllers.hpmca_controller import hpmcaController',
]

print(f'--- {sys.version.split()[0]}  {sys.executable}', flush=True)
for step in STEPS:
    print(f'  ... {step}', flush=True)
    try:
        exec(step)
    except Exception as exc:
        print(f'  FAIL {step}\n       {type(exc).__name__}: {exc}', flush=True)
        break
else:
    print('  ALL OK', flush=True)
