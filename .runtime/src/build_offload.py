import parser.pycparser as pcp

from collections import OrderedDict

class OffloadBuilder:
	
	def __init__(self, kernel_id, kernel_node):
		self._k_id = kernel_id
		self._k_def = kernel_node

		self._match_arr = OrderedDict()
		self._match_arr['u64'] = ['*', 'unsiged long', 'uint64_t']
		self._match_arr['i64'] = ['long', 'int64_t']
		self._match_arr['u32'] = ['unsigned int', 'uint32_t']
		self._match_arr['i32'] = ['int', 'int32_t']
		self._match_arr['u16'] = ['unsigned short', 'uint16_t']
		self._match_arr['i16'] = ['short', 'int16_t']
		self._match_arr['u8'] = ['unsigned char', 'uint8_t']
		self._match_arr['i8'] = ['char', 'int8_t']
		self._match_arr['double'] = ['double']
		self._match_arr['float'] = ['float']

		self._args = self._map_args_veo(self._list_args_types())

	def build_pe_offload_header(self, pg_size):
		return self._func_decl(pg_size)
		
	def build_pe_offload_code(self, pg_size):
		
		# get function to call
		if(pg_size is None):
			ki_id = '%s__omp__' % self._k_id
		else:
			ki_id = '%s__%d__omp__' % (self._k_id, pg_size)

		# start with an empty body
		ki_body = []

		# declare req, retval
		ki_body.append(
			pcp.c_ast.Decl(
				'req',
				[],
				[],
				[],
				pcp.c_ast.TypeDecl(
					'req',
					[],
					pcp.c_ast.IdentifierType(['uint64_t'])),
				None,
				None))
		ki_body.append(
			pcp.c_ast.Decl(
				'retval',
				[],
				[],
				[],
				pcp.c_ast.TypeDecl(
					'retval',
					[],
					pcp.c_ast.IdentifierType(['uint64_t'])),
				None,
				None))

		# clear arguments
		ki_body.append(
			pcp.c_ast.FuncCall(
				pcp.c_ast.ID('veo_args_clear'),
				pcp.c_ast.ExprList([
					pcp.c_ast.ID('_veo_inst.args')
				])))

		# add kernel arguments (pointers as uint64_t!)
		for ix, item in enumerate(self._args):
			ki_body.append(
				pcp.c_ast.FuncCall(
					pcp.c_ast.ID('veo_args_set_%s' % item[0]),
					pcp.c_ast.ExprList([
						pcp.c_ast.ID('_veo_inst.args'),
						pcp.c_ast.ID(str(ix)),
						pcp.c_ast.ID(item[2])
					])))

		# get symbol
		ki_body.append(
			pcp.c_ast.Assignment(
				'=',
				pcp.c_ast.ID('_veo_inst.sym'),
				pcp.c_ast.FuncCall(
					pcp.c_ast.ID('veo_get_sym'),
					pcp.c_ast.ExprList([
						pcp.c_ast.ID('_veo_inst.hproc'),
						pcp.c_ast.Constant(
							pcp.c_ast.IdentifierType(['uint64_t']),
							'0'),
						pcp.c_ast.Constant(
							pcp.c_ast.IdentifierType(['const char *']),
							'\"%s\"' % ki_id)]))))

		# offload kernel call
		ki_body.append(
			pcp.c_ast.Assignment(
				'=',
				pcp.c_ast.ID('req'),
				pcp.c_ast.FuncCall(
					pcp.c_ast.ID('veo_call_async'),
					pcp.c_ast.ExprList([
						pcp.c_ast.ID('_veo_inst.hctxt'),
						pcp.c_ast.ID('_veo_inst.sym'),
						pcp.c_ast.ID('_veo_inst.args')]))))

		# synchronize aurora device
		ki_body.append(
			pcp.c_ast.FuncCall(
				pcp.c_ast.ID('veo_call_wait_result'),
				pcp.c_ast.ExprList([
					pcp.c_ast.ID('_veo_inst.hctxt'),
					pcp.c_ast.ID('req'),
					pcp.c_ast.ID('&retval')])))

		# return implementation
		return pcp.c_ast.FuncDef(
			self._func_decl(pg_size),
			None,
			pcp.c_ast.Compound(ki_body))

	def _func_decl(self, pg_size):
		# kernel variant id includes the PG size
		if(pg_size is None):
			ki_id = '%s__offload__' % self._k_id
		else:
			ki_id = '%s__%d__offload__' % (self._k_id, pg_size)

		# copy param decls from definition + number of jobs parameter
		ki_param_decl = pcp.c_ast.ParamList([])
		for arg in self._args:
			raw_type = self._match_arr[arg[0]][-1]

			ki_param_decl.params.append(pcp.c_ast.Decl(
					arg[2],
					[],
					[],
					[],
					pcp.c_ast.TypeDecl(
						arg[2],
						[arg[1]] if len(arg[1]) > 0 else None,
						pcp.c_ast.IdentifierType([raw_type])),
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

	def _list_args_types(self):

		args = []

		for a_decl in self._k_def.decl.type.args.params:

			# flatten qualifier string
			quals = ''
			if(type(a_decl) == pcp.c_ast.PtrDecl):
				for s in a_decl.type.type.quals:
					quals += s + ' '
			else:
				for s in a_decl.type.quals:
					quals += s + ' '

			quals = quals.strip()

			if(type(a_decl.type) is pcp.c_ast.PtrDecl):
				args.append(('%s *' % a_decl.type.type.type.names[0], quals, a_decl.name))
			else:
				args.append(('int', quals, a_decl.name))
				
		# artificial 'num jobs' argument
		args.append(('int', 'const', '__num_pgs'))

		return args

	def _map_args_veo(self, args):

		def map(arg):
			for _sfx in self._match_arr:
				for expr in self._match_arr[_sfx]:
					if(arg.find(expr) != -1):
						return _sfx
			
			return 'UNKNOWN'

		return [(map(a[0]), a[1], a[2]) for a in args]

class OffloadFileBuilder:

	def __init__(self):
		self._o_header = []
		self._o_code = []

	def add_kernel_instance(self, kernel_id, kernel_node, pg_size):
		bob = OffloadBuilder(kernel_id, kernel_node)

		self._o_header.append(bob.build_pe_offload_header(pg_size))
		self._o_code.append(bob.build_pe_offload_code(pg_size))

	def header_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._o_header))

	def src_ast(self):
		return pcp.c_ast.FileAST(
			pcp.c_ast.DeclList(self._o_code))
