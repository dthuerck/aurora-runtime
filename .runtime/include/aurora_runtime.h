#define __attribute__(x)
#define __extension__

#ifndef __AURORA_RUNTIME
#define __AURORA_RUNTIME

#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <signal.h>

#include <ve_offload.h>
#include <veo_udma.h>

/* fix tag declarations */
#ifdef __VEO_STRUCTS__
typedef struct {} veo_proc_handle;
typedef struct {} veo_thr_ctxt;
typedef struct {} veo_args;
#endif

typedef struct {
    int ve_dev_id;
    int udma_peer_id;
    veo_proc_handle * hproc;
    veo_thr_ctxt * hctxt;
    veo_args * args;
    uint64_t sym;
    uint64_t sym_malloc;
    uint64_t sym_free;
} veo_bundle_t;

extern veo_bundle_t _veo_inst;

typedef union {
    void * ptr;
    uint64_t slot;
} mem_addr_t;

/* ************************************************************************** */

void check(
    const int err, 
    const char* file, 
    const int line);
#define CHECK_VEO(err) ({int v = err; check(v, __FILE__, __LINE__); raise(SIGSEGV); })

/* ************************************************************************** */

int ve_init(const int dev_id);
void ve_finish();

void ve_malloc(
    uint64_t * slot, 
    const size_t bytes);
void ve_free(
    uint64_t slot);

void 
ve_memcpy_h2d(
    uint64_t dst, 
    const void * src, 
    const size_t bytes, 
    int commit);
void 
ve_memcpy_d2h(
    void * dst, 
    uint64_t src, 
    const size_t bytes, 
    int commit);

#endif /* __AURORA_RUNTIME */
