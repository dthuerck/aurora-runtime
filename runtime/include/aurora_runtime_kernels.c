#include <omp.h>
#include <pthread.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

void
ve_init()
{
    #pragma omp parallel
    {
        auto tx = omp_get_thread_num();
        cpu_set_t set;
        memset(&set, 0, sizeof(cpu_set_t));
        set.__bits[0] = 1 << tx;
        pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &set);
    }   
}

void
ve_close()
{
    exit(0);
}

uint64_t
ve_helper_malloc(const size_t sz)
{
  return (uint64_t)malloc(sz);
}

void
ve_helper_free(uint64_t addr)
{
  free((void *)addr);
}
