#include <iostream>
#include <iostream>
#include <random>
#include <cstdlib>
#include <vector>
#include <cstring>
#include <sstream>
#include <signal.h>

#include "timer.h"

/* all generated sources are pure C99 */
extern "C"
{
    /* vital runtime functions */
    #include <aurora_runtime.h>

    /** 
     * kernel file XXX.cve generates a header XXX_offload.h which we need
     * to include here
    */
    #include <gema_offload.h>
    #include <gemm_offload.h>
}

/* ************************************************************************** */

template<typename T>
void 
random_matrix(
    T * mat,
    const int m,
    const int n,
    std::mt19937& rnd_gen)
{
    std::uniform_real_distribution<T> dist(
        static_cast<T>(-1.0), 
        static_cast<T>(1.0));

    for(unsigned int i = 0; i < m * n; ++i)
        mat[i] = dist(rnd_gen);
}

/* ************************************************************************** */

int
main(
    int argc,
    const char * argv[])
{
    using scalar_t = double;
    const int ve_dev_id = 1;
    const int batch = 1000;

    /* initialize the Aurora device */
    std::cout << "Initializing the Aurora..." << std::endl;
    if(ve_init(ve_dev_id) != VEO_COMMAND_OK)
    {
        std::cout << "Failed to initialize the Aurora device, exiting..." <<
            std::endl;
    }
    std::cout << "Done!" << std::endl;

    /* create random matrices for the GEMM */
    const long long int seed = 384562397463248l;
    const int m = 256;
    std::vector<scalar_t> As(m * m * batch, 1.0);
    std::vector<scalar_t> Bs(m * m * batch, 1.0);
    std::vector<scalar_t> GEMA_Cs(m * m * batch, 0.0);
    std::vector<scalar_t> GEMM_Cs(m * m * batch, 0.0);

    START_TIMER("GenData");

    std::cout << "Generating data..." << std::endl;
    #pragma omp parallel for
    for(int s = 0; s < batch; ++s)
    {
        std::mt19937 rnd_gen(seed + s);

        scalar_t * A = As.data() + s * m * m;
        scalar_t * B = Bs.data() + s * m * m;
        scalar_t * GEMA_C = GEMA_Cs.data() + s * m * m;
        scalar_t * GEMM_C = GEMM_Cs.data() + s * m * m;

        random_matrix(A, m, m, rnd_gen);
        random_matrix(B, m, m, rnd_gen);

        /* create GEMA result for comparison */
        for(int i = 0; i < m; ++i)
        {
            for(int j = 0; j < m; ++j)
            {
                /* interpret B as row major */
                GEMA_C[i * m + j] = A[i * m + j] + B[i * m + j];
            }
        }

        /* create GEMM result for comparison */
        for(int i = 0; i < m; ++i)
        {
            for(int j = 0; j < m; ++j)
            {
                for(int l = 0; l < m; ++l)
                {
                    /* interpret B as col major */
                    GEMM_C[i * m + j] += A[i * m + l] * B[l * m + j];
                }
            }
        }
    }
    std::cout << "Done!" << std::endl;

    STOP_TIMER("GenData");
    PRINT_TIMER("GenData");

    /* allocate storage on device */
    uint64_t dev_As, dev_Bs, dev_GEMA_Cs, dev_GEMM_Cs;
    ve_malloc(&dev_As, m * m * batch * sizeof(scalar_t));
    ve_malloc(&dev_Bs, m * m * batch * sizeof(scalar_t));
    ve_malloc(&dev_GEMA_Cs, m * m * batch * sizeof(scalar_t));
    ve_malloc(&dev_GEMM_Cs, m * m * batch * sizeof(scalar_t));

    /* schedule all memcopies - 'commit' on the last call */
    ve_memcpy_h2d(dev_As, As.data(), m * m * batch * sizeof(scalar_t), 0);
    ve_memcpy_h2d(dev_Bs, Bs.data(), m * m * batch * sizeof(scalar_t), 1);

    /* device function calls */
    START_TIMER("Batched GEMA");
    gema_op_d__offload__(dev_As, dev_Bs, dev_GEMA_Cs, batch);
    STOP_TIMER("Batched GEMA");
    PRINT_TIMER("Batched GEMA");
    PRINT_PERF("Batched GEMA", batch*(double)m*(double)m);

    START_TIMER("Batched GEMM");
    gemm_op_d__offload__(dev_As, dev_Bs, dev_GEMM_Cs, batch);
    STOP_TIMER("Batched GEMM");
    PRINT_TIMER("Batched GEMM");
    PRINT_PERF("Batched GEMM", batch*(double)m*(double)m*(double)m*2);

    /* transfer the results back */
    std::vector<scalar_t> d_GEMA_Cs(batch * m * m * sizeof(scalar_t));
    std::vector<scalar_t> d_GEMM_Cs(batch * m * m * sizeof(scalar_t));
    ve_memcpy_d2h(d_GEMA_Cs.data(), dev_GEMA_Cs, m * m * batch * 
        sizeof(scalar_t), 1);
    ve_memcpy_d2h(d_GEMM_Cs.data(), dev_GEMM_Cs, m * m * batch * 
        sizeof(scalar_t), 1);

    /* free device memory */
    ve_free(dev_GEMM_Cs);
    ve_free(dev_GEMA_Cs);
    ve_free(dev_Bs);
    ve_free(dev_As);

    /* check results */
    std::cout << "Checking GEMA results..." << std::endl;
    for(int s = 0; s < batch; ++s)
    {
        const scalar_t * ref_C = GEMA_Cs.data() + s * m * m;
        const scalar_t * d_C = d_GEMA_Cs.data() + s * m * m;

        scalar_t max_err = 0.0;
        for(int i = 0; i < m * m; ++i)
        {
            const scalar_t i_err = std::abs(ref_C[i] - d_C[i]);
            if(i_err > max_err)
            {   
                max_err = i_err;
            }
        }

        if(max_err > 1e-3)
        {
            std::cout << "GEMA: Max err " << max_err << " at item " << s << "..." << std::endl;
        }
    }

    std::cout << "Checking GEMM results..." << std::endl;
    for(int s = 0; s < batch; ++s)
    {
        const scalar_t * ref_C = GEMM_Cs.data() + s * m * m;
        const scalar_t * d_C = d_GEMM_Cs.data() + s * m * m;

        scalar_t max_err = 0.0;
        for(int i = 0; i < m * m; ++i)
        {
            const scalar_t i_err = std::abs(ref_C[i] - d_C[i]);
            if(i_err > max_err)
            {   
                max_err = i_err;
            }
        }

        if(max_err > 1e-3)
        {
            std::cout << "GEMM: Max err " << max_err << " at item " << s << "..." << std::endl;
        }
    }
    std::cout << "Done!" << std::endl;

    /* shutdown the device connection */
    ve_finish();

    return EXIT_SUCCESS;
}
