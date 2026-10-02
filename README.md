# hp-edxd
 
Python-based suite of programs for data collection, viewing and analysis of energy-dispersive x-ray diffraction. The software has specialized features for experiments on materials under high pressure. The software is currently used at beamline 16-BM-B, Advanced Photon Source to acquire, view, and process the x-ray diffraction data.

The programs work with Anaconda Python 3.7 <br>
required python packages: <br>
pyqt5 5.9.2 (Some compatiblity issues with newer versions)<br>
pyqtgraph 0.11.0 (Not compatible with 0.12.0+)<br> 
pyepics 3.4.0<br>
burnman 0.9.0<br>
PyCifRW 4.4.1 <br>
numpy, scipy, natsort, qtpy, pillow, scikit-image (no known version constraint)<br>

The list above is the full set of imports under `hpm/`, `utilities/` and
`mypyeqt/`. See `environment.yml` for a conda environment built from it:

> conda env create -f environment.yml<br>
> conda activate hp-edxd<br>
> python hpMCA.py

That file has not been solved on a clean machine yet — expect to adjust it, and
please pin what worked once it does.

> export PYEPICS_LIBCA=/usr/local/epics/base-7.0.4/lib/linux-x86_64/libca.so
To find out which CA library will be used by pyepics, use:
>>> import epics
>>> epics.ca.find_libca()

### Command line

`python hpMCA.py` with no arguments behaves as it always has. To start it with
something already open — this is how the Bluesky/BITS console launches it:

> python hpMCA.py --file spectrum.hpmca<br>
> python hpMCA.py --folder /path/to/scan/ --calibration energy.hpmca<br>
> python hpMCA.py --detector 16bmbDante:mca1

`--detector` opens the record in **live view**, where hpMCA writes calibration,
ROIs and acquisition commands to it. Do not point it at a record another client
is also driving.

### Executables

Executable versions for Windows, Mac OS (all 64bit) can be downloaded from:

https://github.com/hp-edxd/hp-edxd/releases

The executable versions are self-contained and do not need a python installation.

The documentation is hosted at https://hp-edxd.readthedocs.io/.