# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

#[=======================================================================[.rst:
FindAurora
-------

This package locates all necessary components of the NEC AURORA TSUBASA
toolkit and enables a build flow that very much resembles that of 
NVIDIA's CUDA experience.

Input Variables
^^^^^^^^^^^^^^^

``AURORA_UDMA_PATH``
  Path to the UDMA library for Aurora.

Result Variables
^^^^^^^^^^^^^^^^

This will define the following variables:

``AURORA_FOUND``
  True if the system has all necessary components..
``AURORA_INCLUDE_DIRS``
  Include directories needed to use Foo.
''AURORA_LIBRARY_DIRS''
  Folders containing libraries to link against.
``AURORA_LIBRARIES``
  Libraries needed to link to the Aurora object file.
``AURORA_OBJECTS``
  Object files needed to link to the Aurora object file.
``AURORA_VERSION``
  Version number of this package.

Cache Variables
^^^^^^^^^^^^^^^

The following cache variables may also be set:

``AURORA_VECC_SCRIPT``
  Location of the vecc python script.
``AURORA_NCC_EXECUTABLE``
  Location of the ncc compiler.
``AURORA_NCPP_EXECUTABLE``
  Location of the nc++ compiler.
``AURORA_CLANG_EXECUTABLE``
  Location of the clang executable including aurora support.
``AURORA_CLANGPP_EXECUTABLE``
  Location of the clang executable including aurora support.
``AURORA_MKVEORUNSTATIC_EXECUTABLE``
  Location of the mk_veorun_static executable.

#]=======================================================================]

# basic variables
set(AURORA_VERSION "0.2")

# define some basic paths where to look at
set(AURORA_BASE_PATHS 
	"/opt/nec" 
	${AURORA_SEARCH_PATHS}
	${CMAKE_SOURCE_DIR})

# include functions for the build systems
include(find_functions)
include(build_functions)

# find the vecc script
find_file_rec_cached(AURORA_VECC_SCRIPT "vecc.py" "${AURORA_BASE_PATHS}")
find_file_rec_cached(AURORA_SYMBOL_TABLE_SCRIPT "symbol_table.py" "${AURORA_BASE_PATHS}")

# find ncc / nc++
find_file_rec_cached(AURORA_NCC_EXECUTABLE "ncc" "${AURORA_BASE_PATHS}")
find_file_rec_cached(AURORA_NCPP_EXECUTABLE "nc++" "${AURORA_BASE_PATHS}")

# find LLVM / clang
find_file_rec_cached(AURORA_CLANG_EXECUTABLE "clang" "${AURORA_BASE_PATHS}")
find_file_rec_cached(AURORA_CLANGPP_EXECUTABLE "clang++" "${AURORA_BASE_PATHS}")

# find veorun
find_file_rec_cached(AURORA_MKVEORUNSTATIC_EXECUTABLE "mk_veorun_static" "${AURORA_BASE_PATHS}")

# find include directories
find_path_rec_cached(__AURORA_VEOFFLOAD_INCLUDE_DIR "ve_offload.h" "${AURORA_BASE_PATHS}")
find_path_rec_cached(__AURORA_INTRINSIC_INCLUDE_DIR "velintrin.h" "${AURORA_BASE_PATHS}")
find_path_rec_cached(__AURORA_UDMA_INCLUDE_DIR "veo_udma.h" "${AURORA_BASE_PATHS}")
find_path_rec_cached(__AURORA_RUNTIME_INCLUDE_DIR "aurora_runtime.h" "${AURORA_BASE_PATHS}")

set(AURORA_INCLUDE_DIRS
	${__AURORA_VEOFFLOAD_INCLUDE_DIR}
	${__AURORA_RUNTIME_INCLUDE_DIR}
	${__AURORA_UDMA_INCLUDE_DIR})

# find library directories
find_path_rec_cached(__AURORA_VEIO_LIB_DIR "libveio.so" "${AURORA_BASE_PATHS}")
find_path_rec_cached(__AURORA_VEO_LIB_DIR "libveo.so" "${AURORA_BASE_PATHS}")
find_path_rec_cached(__AURORA_NCPP_LIB_DIR "libnc++.so" "${AURORA_BASE_PATHS}")

set(AURORA_LIBRARY_DIRS 
	${__AURORA_VEIO_LIB_DIR} 
	${__AURORA_VEO_LIB_DIR}
	${__AURORA_NCPP_LIB_DIR}) 

# set libraries
set(AURORA_LIBRARIES
	"veio"
	"nc++"
	"pthread")

# find object files for mk_veorun_static
find_file_rec_cached(__AURORA_UDMA_VE_LIB "libveo_udma_ve.o" "${AURORA_BASE_PATHS}")
find_file_rec_cached(__AURORA_UDMA_VH_LIB "libveo_udma.o" "${AURORA_BASE_PATHS}")

set(AURORA_OBJECTS
	${__AURORA_UDMA_VE_LIB})

# set parameters for compiling
set(AURORA_LCFLAGS -std=c99 -target ve -O3 -fno-vectorize -fno-slp-vectorize -fno-crash-diagnostics)
set(AURORA_NCFLAGS -std=c99 -pthread -O3 -fopenmp -Wl,-zdefs -rdynamic -report-all -fdiag-vector=2 -fdiag-inline=2 -fdiag-parallel=2)
set(AURORA_CFLAGS -std=gnu89 -O3 -pthread -fopenmp -Wl,-zdefs -rdynamic)

# set paths for host compiler
include_directories(SYSTEM
	${AURORA_INCLUDE_DIRS}
	${CMAKE_BINARY_DIR}
	${CMAKE_BINARY_DIR}/ve_offload)

link_directories(
	${AURORA_LIBRARY_DIRS})

# list of libraries for host executables using VE
set(AURORA_HOST_LIBRARIES
	veo
	${__AURORA_UDMA_VH_LIB})