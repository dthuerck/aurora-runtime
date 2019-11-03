#pragma once

/**
 * Copyright (c) 2016, NVIDIA CORPORATION. All rights reserved.
 * Copyright (c) 2017, Daniel Thuerck, TU Darmstadt - GCC. All rights reserved.
 *
 * This software may be modified and distributed under the terms
 * of the BSD 3-clause license. See the LICENSE file for details.
 */

#include <stdint.h>
#include <chrono>
#include <map>
#include <string>

/* timing utils */
using t_point = std::chrono::time_point<std::chrono::system_clock>;
struct _timer
{
    _timer();
    ~_timer();

    void start(const std::string& s);
    void stop(const std::string& s);
    void clear(const std::string& s);
    double get_ms(const std::string& s);

    std::map<std::string, t_point> m_t_start;
    std::map<std::string, double> m_t_accu;
    std::map<std::string, t_point> m_t_end;
};

extern _timer * __T;

#define START_TIMER(str) (__T->start(str));
#define CLEAR_TIMER(str) (__T->clear(str));
#define STOP_TIMER(str) (__T->stop(str));
#define PRINT_TIMER(str) (printf("(Timing) %s: %f ms\n", str, __T->get_ms(str)));
#define PRINT_REPEAT_TIMER(str, ctr) (printf("(Timing) %s: %f ms\n", str, __T->get_ms(str) / ctr));
#define GET_TIMER(str) (__T->get_ms(str))