import parser.pycparser as pcp

class WrapperBuilder:

	def __init__(self, kernel_id, kernel_node):
		self._k_id = kernel_id
		self._k_def = kernel_node

	def build_pe_wrapper_header(self, pg_size):
		return self._func_decl(pg_size)

	def build_pe_wrapper_code(self, pg_size):

		# get function to call
		if(pg_size is None):
			ki_id = '%s__' % self._k_id
		else:
			ki_id = '%s__%d__' % (self._k_id, pg_size)

		# PG size to use
		print_pg_size = pg_size if pg_size is not None else 1
		
		# start with an empty body
		ki_body = []
		ki_body.append(pcp.c_ast.Pragma('omp parallel for'))
		ki_body.append(pcp.c_ast.For(
			# init
			pcp.c_ast.Decl(
				'_omp_ix',
				[],
				[],
				[],
				pcp.c_ast.TypeDecl(
					'_omp_ix',
					[],
					pcp.c_ast.IdentifierType(['int'])),
				pcp.c_ast.Constant(
					'int',
					'0'),
				None),
			# cond
			pcp.c_ast.BinaryOp(
				'<',
				pcp.c_ast.ID('_omp_ix'),
				pcp.c_ast.ID('__num_pgs')),
			# next
			pcp.c_ast.UnaryOp(
				'++',
				pcp.c_ast.ID('_omp_ix')),

			# stmt
			pcp.c_ast.FuncCall(
				pcp.c_ast.ID(ki_id),
				pcp.c_ast.ExprList([
					*[pcp.c_ast.ID(arg.name) for arg in self._k_def.decl.type.args.params],
					pcp.c_ast.Constant(
						'int',
						str(print_pg_size)),
					pcp.c_ast.ID('_omp_ix'),
					pcp.c_ast.ID('__num_pgs')]))
		))

		return pcp.c_ast.FuncDef(
			self._func_decl(pg_size),
			None,
			pcp.c_ast.Compound(ki_body))

	def _func_decl(self, pg_size):
		# kernel variant id includes the PG size
		if(pg_size is None):
			ki_id = '%s__omp__' % self._k_id
		else:
			ki_id = '%s__%d__omp__' % (self._k_id, pg_size)

		# copy param decls from definition + number of jobs parameter
		ki_param_decl = pcp.c_ast.ParamList([
			*self._k_def.decl.type.args.params,
			pcp.c_ast.Decl(
				'__num_pgs',
				['const'],
				[],
				[],
				pcp.c_ast.TypeDecl(
					'__num_pgs',
					[],
					pcp.c_ast.IdentifierType(['int'])),
				None,
				None)])

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

	def _func_name(self, pg_size):
		# kernel variant id includes the PG size
		if(pg_size is None):
			ki_id = '"%s__omp__"' % self._k_id
		else:
			ki_id = '"%s__%d__omp__"' % (self._k_id, pg_size)
		return pcp.c_ast.Constant('string', ki_id)


class WrapperFileBuilder:

	def __init__(self):
		self._w_header = []
		self._w_code = []
		self._w_func_names = [] 

	def add_kernel_instance(self, kernel_id, kernel_node, pg_size):
		bob = WrapperBuilder(kernel_id, kernel_node)

		self._w_header.append(bob.build_pe_wrapper_header(pg_size))
		self._w_code.append(bob.build_pe_wrapper_code(pg_size))

	def header_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._w_header))

	def src_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._w_code))
