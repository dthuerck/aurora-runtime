#include <stdio.h>

#include "aurora_runtime.h"
#include <ve_kernel_names.h>

veo_bundle_t _veo_inst;

/* ************************************************************************** */

void 
check(
    const int err, 
    const char* file, 
    const int line) 
{
	if(err != VEO_COMMAND_OK) {
		switch(err) {
			case VEO_COMMAND_EXCEPTION:		
                printf("[VE] VEO_COMMAND_EXCEPTION in %s@%d\n", file, line);
                break;
			case VEO_COMMAND_ERROR:			
                printf("[VE] VEO_COMMAND_ERROR in %s@%d\n", file, line);
                break;
			case VEO_COMMAND_UNFINISHED:	
                printf("[VE] VEO_COMMAND_UNFINISHED in %s@%d\n", file, line);
                break;
            default: 
                printf("[VE] UNKNWON in %s@%d\n", file, line);
                break;
		}
	}
}

/* ************************************************************************** */

int 
ve_init(
    const int dev_id)
{
    _veo_inst.ve_dev_id = dev_id;

    _veo_inst.hproc = veo_proc_create_static(_veo_inst.ve_dev_id, 
        "ve_kernels.o");
    if(_veo_inst.hproc == NULL)
    {
        printf("[VE] Handle is NULL, exiting...");
        return VEO_COMMAND_ERROR;
    }
    uint64_t init_sym = veo_get_sym(_veo_inst.hproc, 0UL, "ve_init");
    _veo_inst.sym_malloc = veo_get_sym(_veo_inst.hproc, 0UL, "ve_helper_malloc");
    _veo_inst.sym_free = veo_get_sym(_veo_inst.hproc, 0UL, "ve_helper_free");

    /*
      Find all kernel function symbol addresses before creating the context.
      This is a workaround for VEO not scheduling properly on 8 cores.
    */
    int i = 0;
    char *c = _ve_kernel_funcs_[0];
    for(; *c != '\0'; c = _ve_kernel_funcs_[++i]) {
        uint64_t _dummy = veo_get_sym(_veo_inst.hproc, 0, c);
    }

    _veo_inst.hctxt = veo_context_open(_veo_inst.hproc);
    if(_veo_inst.hctxt == NULL)
    {
        printf("[VE] Context is NULL, exiting...");
        return VEO_COMMAND_ERROR;
    }

    _veo_inst.args = veo_args_alloc();
    veo_args_clear(_veo_inst.args);
    
    uint64_t req = veo_call_async(_veo_inst.hctxt, init_sym, _veo_inst.args);
    
    uint64_t retval;
    CHECK_VEO(veo_call_wait_result(_veo_inst.hctxt, req, &retval));

    _veo_inst.udma_peer_id = veo_udma_peer_init(_veo_inst.ve_dev_id,
                                _veo_inst.hproc, _veo_inst.hctxt, 0);
    
    return VEO_COMMAND_OK;
}

/* ************************************************************************** */

void 
ve_finish()
{
    veo_args_free(_veo_inst.args);
    veo_udma_peer_fini(_veo_inst.udma_peer_id);

    CHECK_VEO(veo_context_close(_veo_inst.hctxt));
    CHECK_VEO(veo_proc_destroy(_veo_inst.hproc));
}

/* ************************************************************************** */

void 
ve_malloc(
    uint64_t * slot, 
    const size_t bytes)
{
    uint64_t retval;
    veo_args_clear(_veo_inst.args);
    veo_args_set_u64(_veo_inst.args, 0, bytes);
    uint64_t req = veo_call_async(_veo_inst.hctxt, _veo_inst.sym_malloc,
                                  _veo_inst.args);
    CHECK_VEO(veo_call_wait_result(_veo_inst.hctxt, req, &retval));
    *slot = retval;
}

/* ************************************************************************** */

void
ve_free(
    uint64_t slot)
{
    uint64_t retval;
    veo_args_clear(_veo_inst.args);
    veo_args_set_u64(_veo_inst.args, 0, slot);
    uint64_t req = veo_call_async(_veo_inst.hctxt, _veo_inst.sym_free,
                                  _veo_inst.args);
    CHECK_VEO(veo_call_wait_result(_veo_inst.hctxt, req, &retval));
}

/* ************************************************************************** */

void 
ve_memcpy_h2d(
    uint64_t dst, 
    const void * src, 
    const size_t bytes, 
    int commit)
{
    veo_udma_send_pack(
        _veo_inst.udma_peer_id,
        src,
        (uint64_t) dst,
        bytes);

    if(commit)
        veo_udma_send_pack_commit(_veo_inst.udma_peer_id);
}

void 
ve_memcpy_d2h(
    void * dst, 
    uint64_t src, 
    const size_t bytes, 
    int commit)
{
    veo_udma_recv_pack(
        _veo_inst.udma_peer_id,
        (const uint64_t) src,
        dst,
        bytes);

    if(commit)
        veo_udma_recv_pack_commit(_veo_inst.udma_peer_id);
}
