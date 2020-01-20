import os
import sys
import argparse
import re

import parser.pycparser as pcp
import parser.pycparser.c_generator

from src.find_kernels import *
from src.build_kernels import *
from src.build_wrappers import *
from src.build_offload import *

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':

    cwd = os.getcwd()

    # parse includes, input file & output locations (plus debug options)
    cmdparser = argparse.ArgumentParser(description="A compiler-driver for NEC Aurora Kernels.")
    cmdparser.add_argument('--includedir', action='append',
        help='Additional include paths for the parser')

    cmdparser.add_argument('--kerneldir', help='Output directory for generated kernel files.',
        default='%s/gen/kernels' % cwd)
    cmdparser.add_argument('--wrapperdir', help='Output directory for generated wrapper files.',
        default='%s/gen/wrappers' % cwd)
    cmdparser.add_argument('--offloaddir', help='Output directory for generated offload files.',
        default='%s/gen/offload' % cwd)
    cmdparser.add_argument('in_file', help='Input file in .cve format.')
    cmdparser.add_argument('--verbose', help='Print generated output files.')

    cmdargs = cmdparser.parse_args()

    ##
    # Parse .cve file with modified lexer and parser to extract 
    # Aurora Kernels
    ##
    cur_path = os.path.dirname(os.path.realpath(__file__))
    cpp_path = 'cpp'
    cpp_args = [
        '-std=c99',
        '-D__VECC__',
        # '-I%s/../header' % cur_path,
        '-I%s/parser/utils/fake_libc_include' % cur_path,
        '-I%s/include' % cur_path]
    for path in cmdargs.includedir:
        cpp_args.append('-I%s' % path)

    # run C preprocessor first
    text = pcp.preprocess_file(cmdargs.in_file, cpp_path, cpp_args)

    # remove all preprocessor directives
    cpp_regex = r'\#.*\n'
    text = re.sub(cpp_regex, '', text)

    # while developing, set this flag to True
    rebuild = False
    parser = pcp.c_parser.CParser(
        lex_optimize=not rebuild,
        yacc_optimize=not rebuild,
        taboutputdir='%s/parser/pycparser' % cur_path)
    ast = parser.parse(text, cmdargs.in_file)

    # dump AST
    # ast.show(showcoord = False)

    # find all kernels and their configuration
    kern = LocateKernels()
    kern.visit(ast)
    kern.print_kernels()
    ids = kern.get_kernel_ids()
    
    # generate source code & wrappers for kernels found
    k_builder = KernelFileBuilder()
    w_builder = WrapperFileBuilder()
    o_builder = OffloadFileBuilder()
    for k_id in ids:
        pgs = []
        if(kern[k_id][0] is None):
            pgs = [None]
        else:
            pgs = kern[k_id][0]

        for pg_size in pgs:
            k_builder.add_kernel_instance(k_id, kern[k_id][1], pg_size)
            w_builder.add_kernel_instance(k_id, kern[k_id][1], pg_size)
            o_builder.add_kernel_instance(k_id, kern[k_id][1], pg_size)

    # get basename of current file
    in_base_name = os.path.splitext(os.path.basename(cmdargs.in_file))[0]

    # generate output files
    generator = pcp.c_generator.CGenerator()

    gen_jobs = [
        (
            '%s/%s_kernels.h' % (cmdargs.kerneldir, in_base_name),
            k_builder.header_ast(),
            []
        ),
        (
            '%s/%s_kernels.c' % (cmdargs.kerneldir, in_base_name),
            k_builder.src_ast(),
            [
                '#include <velintrin.h>',
                '#include <velintrin_gen.h>',
                '#include <velintrin_approx.h>'
            ]
        ),
        (
            '%s/%s_wrappers.h' % (cmdargs.wrapperdir, in_base_name),
            w_builder.header_ast(),
            []
        ),
        (
            '%s/%s_wrappers.c' % (cmdargs.wrapperdir, in_base_name),
            w_builder.src_ast(),
            [
                '#include \"../ve_kernels/%s_kernels.h\"' % in_base_name,
                '#include <omp.h>'
            ]
        ),
        (
            '%s/%s_offload.h' % (cmdargs.offloaddir, in_base_name),
            o_builder.header_ast(),
            []
        ),
        (
            '%s/%s_offload.c' % (cmdargs.offloaddir, in_base_name),
            o_builder.src_ast(),
            [
                '#include \"aurora_runtime.h\"',
            ]
        )
    ]

    for job in gen_jobs:

        if(cmdargs.verbose):
            print('\n\n')
            print('================================')
            print(job[0])
            print('================================')
            print('\n')
        gen_code = generator.visit(job[1])
        
        with open(job[0], 'w') as f:
            if(len(job[2]) > 0):
                for tok in job[2]:
                    f.write('%s\n' % tok)
                f.write('\n\n')
            f.write(gen_code)

        if(cmdargs.verbose):
            with open(job[0], 'r') as f:
                print(f.read())
