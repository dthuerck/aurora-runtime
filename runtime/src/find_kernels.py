import parser.pycparser as pcp

class LocateKernels(pcp.c_ast.NodeVisitor):

    def __init__(self):
        super().__init__()

        self._kernels = {}

    def visit_KernelDef(self, node):

        # parse kernel name
        fun_id = node.decl.name

        # parse kernel configuration values [list of int] or None
        configs = None if not hasattr(node.config, 'exprs') else [int(e.value) for e in node.config.exprs]

        # save kernel
        if(fun_id in self._kernels):
            print('Duplicate definition for kernel %s...' % fun_id)
        else:
            self._kernels[fun_id] = (configs, node)

    def get_kernel_ids(self):
        return self._kernels.keys()

    def __getitem__(self, key):
        return self._kernels[key]

    def print_kernels(self):
        print('Kernel functions discovered:')
        for kern in self._kernels:
            print('  ', kern, ':', self._kernels[kern][0])