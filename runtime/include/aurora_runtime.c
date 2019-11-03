#include <stdio.h>

#include "aurora_runtime.h"

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
    _veo_inst.hctxt = veo_context_open(_veo_inst.hproc);
    if(_veo_inst.hctxt == NULL)
    {
        printf("[VE} Context is NULL, exiting...");
        return VEO_COMMAND_ERROR;
    }

    _veo_inst.args = veo_args_alloc();
    veo_args_clear(_veo_inst.args);

    _veo_inst.udma_peer_id = veo_udma_peer_init(_veo_inst.ve_dev_id, 
        _veo_inst.hproc, _veo_inst.hctxt, 0);

    uint64_t init_sym = veo_get_sym(_veo_inst.hproc, 0UL, "ve_init");
    uint64_t req = veo_call_async(_veo_inst.hctxt, init_sym, _veo_inst.args);

    uint64_t retval;
    CHECK_VEO(veo_call_wait_result(_veo_inst.hctxt, req, &retval));

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
    CHECK_VEO(veo_alloc_mem(_veo_inst.hproc, slot, bytes));
}

/* ************************************************************************** */

void 
ve_free(
    uint64_t slot)
{
    CHECK_VEO(veo_free_mem(_veo_inst.hproc, slot));
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