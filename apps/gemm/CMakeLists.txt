cmake_minimum_required(VERSION 3.12)
project(aurora-gemm)

# host compiler settings
set(CC "gcc")
set(CXX "g++")
set(CFLAGS "-std=c++11 -O3 -pthread -fopenmp -Wl,-zdefs -rdynamic")

set(CMAKE_C_COMPILER "${CC}")
set(CMAKE_CXX_COMPILER "${CXX}")
set(CMAKE_C_FLAGS "${CFLAGS}")
set(CMAKE_CXX_FLAGS "${CFLAGS}")

# append the local cmake files to the cmake module path
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/../../runtime/cmake")

# list directories where Aurora SDK components may reside
set(AURORA_SEARCH_PATHS 
    "/opt/nec")

# finally, find SDK paths and import build functions
find_package(Aurora REQUIRED)

# build all kernel components (object files are stored in VE_OBJECTS)
ve_build_offload(gemm.cve)

# build main executable and link device objects
ve_add_executable(app-gemm
    timer.cc
    app-gemm.cc)