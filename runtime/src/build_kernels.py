import copy
import parser.pycparser as pcp

class KernelBuilder:

	def __init__(self, kernel_id, kernel_node):
		self._k_id = kernel_id
		self._k_def = kernel_node

	def build_pe_kernel_header(self, pg_size):
		return self._func_decl(pg_size)

	def build_pe_kernel_code(self, pg_size):

		# start with an empty body
		# ki_body = pcp.c_ast.Compound([])

		# clone body of input
		ki_body = copy.deepcopy(self._k_def.body)

		return pcp.c_ast.FuncDef(
			self._func_decl(pg_size),
			None,
			ki_body)

	def _func_decl(self, pg_size):
		# kernel variant id includes the PG size
		if(pg_size is None):
			ki_id = '%s__' % self._k_id
		else:
			ki_id = '%s__%d__' % (self._k_id, pg_size)

		# copy param decls from definition
		ki_param_decl = copy.deepcopy(self._k_def.decl.type.args)

		# add pseudovariables for processing groups' sizes and ids
		ki_param_decl.params.append(pcp.c_ast.Decl(
			'__pg_size',
			['const'],
			[],
			[],
			pcp.c_ast.TypeDecl(
				'__pg_size',
				['const'],
				pcp.c_ast.IdentifierType(['int'])
			),
			None,
			None))
		ki_param_decl.params.append(pcp.c_ast.Decl(
			'__pg_ix',
			['const'],
			[],
			[],
			pcp.c_ast.TypeDecl(
				'__pg_ix',
				['const'],
				pcp.c_ast.IdentifierType(['int'])
			),
			None,
			None))
		ki_param_decl.params.append(pcp.c_ast.Decl(
			'__num_pgs',
			['const'],
			[],
			[],
			pcp.c_ast.TypeDecl(
				'__num_pgs',
				['const'],
				pcp.c_ast.IdentifierType(['int'])
			),
			None,
			None))

		return pcp.c_ast.Decl(
			ki_id,
			[],
			[],
			[],
			pcp.c_ast.FuncDecl(
				ki_param_decl,
				pcp.c_ast.TypeDecl(
					ki_id,
					[],
					pcp.c_ast.IdentifierType(['void'])
				)
			),
			None,
			None)

class KernelFileBuilder:

	def __init__(self):
		self._k_header = []
		self._k_code = []

	def add_kernel_instance(self, kernel_id, kernel_node, pg_size):
		bob = KernelBuilder(kernel_id, kernel_node)

		self._k_header.append(bob.build_pe_kernel_header(pg_size))
		self._k_code.append(bob.build_pe_kernel_code(pg_size))

	def header_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._k_header))

	def src_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._k_code))

		