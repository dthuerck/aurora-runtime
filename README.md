# aurora-runtime

This package is an attempt to reproduce **NVIDIA's CUDA Runtime API**[1], i.e.
enable the user to write device _kernels_  and launch them in a quasi-_grid_
structure on NEC's Aurora SX-TSUBASA vector engine.

To that end, we wrap NEC's VE Offload [2] and UDMA [3] APIs their such that
the usage mimics CUDA's runtime API.

## Installation and Example

The installation is as easy as a breeze! The dependencies on the target
systems are:

* python (>= 3.5)
* cmake (>= 3.10)
* reasonably new gcc/g++ (eg. from scl devtoolset-8)
* NEC Aurora SDK (ncc, libs) - under ``/opt/nec``
* LLVM-VE (llvm/clang): https://sx-aurora.com/repos/veos/ef_extra under ``/opt/nec``

For installation, 

1. Clone this repository:
    ```
    $ git clone https://github.com/dthuerck/aurora_runtime.git
    ```
2. Download and build dependencies:
    ```
    $ cd aurora_runtime
    $ chmod +x init.sh
    $ ./init.sh
    ```

That's it! Now we can build an example application featuring GEMA (256x256
batched matrix addition) and GEMM (256x256 batched matrix multiplication):

```
$ mkdir build && cd build
$ cmake ..
$ make
```

Finally, run the example with ``./app-test`` and watch your Aurora hard at work!

## Using the runtime

The runtime API functions are listed in ``.runtime/include/aurora_runtime.h``,
their usage is demonstrated in the example (see ``app-test.cc``).

The runtime centers around the concept of a (_virtual_) **processing group**;
basically, we write _kernels_ and each kernel is then executed in a batch
of size ``n`` via offload and OpenMP. Roughly speaking (for people familiar with CUDA),
each processing group is a block and the batch corresponds to a grid of
size ``n``.
The runtime offers the following variables that are set in kernel functions:
* ``__pg__ix``: the index of the processing group (index in the batch)
* ``__num_pgs``: the batch size / number of processing groups
* ``__pe__ix`` / ``__pg_size``: reserved for future use

Lastly, the most important part: kernels are conventional C-functions with
the annotation **__ve_kernel__** and saved with a ``.cve`` extension.

The build process is fully automated and supported by CMake. For details,
please refer to ``CMakeLists.txt``.

## Creating a new project

Ideally, use this repository as a scaffolding:
1. Clone this repository and run the ``init.sh``.
2. Replace ``gema.cve``, ``gemm.cve`` by your kernels.
3. Replace ``app-test.cc`` by your application's source.
4. Change the ``CMakeLists.txt`` accordingly.

That's it!

## Standing on the shoulder of giants...

This project uses the following packages:

* VE Offload [1]
* VE UDMA [2]
* [NEC's LLVM](https://github.com/sx-aurora-dev/llvm-project.git)
* [pycparse](https://github.com/eliben/pycparser)

## References

1. [NVIDIA C Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html)
2. [VE Offload](https://github.com/SX-Aurora/veoffload)
3. [VE UDMA](https://github.com/SX-Aurora/veo-udma)