Transmission-python
===================

Python bindings for Transmission (http://www.transmissionbt.com/)

Build requirements
===================

pybindgen to generate the C++ binding code (needs the py3k patched version --> https://code.launchpad.net/~dan-eicher/pybindgen/py3k)

python 2.x to run pybindgen

python3 >= 3.3 (using a couple functions added in 3.3, will fix this to run on earlier py3k versions eventually...)

Building
===================

 * Patch Transmission with "transmission_python.patch" (exposes a couple functions and adds -fPIC to the static libs) and build:

patch -p0 < ../Transmission-python/transmission_python.patch

./autogen.sh

make

 * Generate the python bindings with:

python modulegen.py

 * Edit setup.py to point "tr_build_dir" at the directory where Transmission was built and build with:

python3 setup.py build

Using
===================

TODO: still debugging...

