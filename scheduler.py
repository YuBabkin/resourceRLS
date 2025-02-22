#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# главное условие: R_observ + R_traker + R_voko = 100%

def scheduler_simple(time_step, res_observ, res_detect, res_tracker, res_voko, res_pk, res_fk, res_fault):
    """
    # # # # # ПЛАНИРОВЩИК, первый, тупейший вариант
    # # временной ресурс на поиск рассчитывается как остаток ресурса после выполнения остальных задач
    """

    res_observ_out = time_step \
                    - res_tracker \
                    - res_voko \
                    - res_pk * time_step \
                    - res_fk * time_step \
                    - res_fault * time_step
    if  (res_observ_out < 0):
        res_observ_out = 0

    res_detect_out = res_detect
    res_tracker_out = res_tracker
    res_voko_out = res_voko
    res_pk_out = res_pk
    res_fk_out = res_fk

    return [res_observ_out, res_detect_out, res_tracker_out, res_voko_out, res_pk_out, res_fk_out]


def scheduler_second(time_step, res_observ, res_detect, res_tracker, res_voko, res_pk, res_fk, res_fault):
    """ ПЛАНИРОВЩИК. Оставшийся ресурс на сопровождение.
    """
    res_in = [res_fault, res_fk, res_pk, res_voko, res_tracker, res_detect, res_observ]
    res_out = [0] * len(res_in)

    sum_res = 0
    for i in range(len(res_in)-1):  # для всех кроме поиска, на поиск всё оставшиеся
        if (sum_res + res_in[i]) >= 1:
            res_out[i] =  1 - sum_res
            sum_res = 1
        else:
            res_out[i] = res_in[i]
            sum_res += res_in[i]

    res_observ_out = 1 - sum_res

    # res_observ_out = res_out[6]
    res_detect_out = res_out[5]
    res_tracker_out = res_out[4]
    res_voko_out = res_out[3]
    res_pk_out = res_out[2]
    res_fk_out = res_out[1]

    return [res_observ_out, res_detect_out, res_tracker_out, res_voko_out, res_pk_out, res_fk_out]
