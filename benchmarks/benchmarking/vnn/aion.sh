#!/bin/bash



# module load lang/Python/3.8.6-GCCcore-10.2.0

module load tools/binutils/2.40-GCCcore-13.2.0
module load devel/CMake/3.27.6-GCCcore-13.2.0
module load tools/GLPK/5.0-GCCcore-13.2.0

export BOOST_ROOT=$HOME/boost_1_84_0_install
export BOOST_INCLUDEDIR=$BOOST_ROOT/include
export BOOST_LIBRARYDIR=$BOOST_ROOT/lib

export LD_LIBRARY_PATH=$HOME/protobuf-3.20.3-install/lib:$LD_LIBRARY_PATH
export PATH=$HOME/Protobuf-3.20.3-install/bin:$PATH
