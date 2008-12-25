#!/bin/sh
# Super ghetto build script

if [ ! -e PATCHED ] 
then 
  # Apply patches
  for i in patches/*.diff
  do
    patch -p0 < $i
  done
  echo "Patches applied" > PATCHED
fi

# Run individual build mechanisms

cd lorcon-svn
./configure && make -j4
cd ..

cd pylorcon-svn
python setup.py build
cd ..

cd pypcap-svn
make -j4
cd ..

