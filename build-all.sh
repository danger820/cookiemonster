#!/bin/sh

cd lorcon-svn
./configure && make -j4
cd ..

cd pylorcon-svn
python setup.py build
cd ..

cd pypcap-svn
make -j4
cd ..

