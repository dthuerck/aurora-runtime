import os
import sys
import argparse
import re
import glob

import parser.pycparser as pcp
import parser.pycparser.c_generator

from src.find_kernels import GetFunctionTable

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':

    cwd = os.getcwd()

    # parse arguments
    cmdparser = argparse.ArgumentParser(description="Collecting symbols for VEOS symbol table.")
    cmdparser.add_argument('--wrapperdir', help='Output directory for generated wrapper files.',
        default='%s/gen/wrappers' % cwd)
    cmdparser.add_argument('out_folder', help='Where to put the ve_kernel_names.h.')

    cmdargs = cmdparser.parse_args()
    cur_path = os.path.dirname(os.path.realpath(__file__))

    # open all kernel wrapper files and query for function names
    wrapper_funs = []

    print('Querying symbols:')
    fun_table_gen = GetFunctionTable()
    for wrap_path in glob.glob('%s/*_wrappers.h' % cmdargs.wrapperdir):
        with open(wrap_path, 'r') as f:
            text = f.read()

        # read file to ast
        rebuild = False
        parser = pcp.c_parser.CParser(
            lex_optimize=not rebuild,
            yacc_optimize=not rebuild,
            taboutputdir='%s/parser/pycparser' % cur_path)
        f_ast = parser.parse(text, f)

        # collect kernels
        fun_table_gen.kernels([])
        fun_table_gen.visit(f_ast)
        print('  ', os.path.basename(wrap_path), '->', fun_table_gen.kernels())

        wrapper_funs += fun_table_gen.kernels()

    # create a single file listing all kernels
    wrapper_funs.append('""')
    symbol_table_ast = pcp.c_ast.FileAST([
        pcp.c_ast.Decl(
            name='_ve_kernel_funcs_',
            quals=['const'],
            storage=[],
            funcspec=[],
            type=pcp.c_ast.ArrayDecl(
                type=pcp.c_ast.PtrDecl(quals=[],
                    type=pcp.c_ast.TypeDecl(
                    '_ve_kernel_funcs_',
                    ['const'],
                    type=pcp.c_ast.IdentifierType(names=['char'])
                )
                ),
                dim=None,
                dim_quals=[]
            ),
            init=pcp.c_ast.InitList([
                pcp.c_ast.Constant('const char *', '"%s"' % val) for val in wrapper_funs
            ]),
            bitsize=None
        ),
    ])

    # export file as ve_kernel_names.h
    generator = pcp.c_generator.CGenerator()
    gen_code = generator.visit(symbol_table_ast)

    out_path = os.path.join(cmdargs.out_folder, 've_kernel_names.h')
    with open(out_path, 'w') as f:
        f.write(gen_code)