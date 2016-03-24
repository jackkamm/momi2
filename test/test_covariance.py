import pytest
import os, random
import autograd.numpy as np

from momi import Demography, simulate_ms
import momi
from test_ms import ms_path

from demo_utils import simple_three_pop_demo, simple_nea_admixture_demo

import scipy

def check_cov(method, params, demo_func, num_runs, theta, bounds=None, **kwargs):
    true_demo = demo_func(*params)
    seg_sites = simulate_ms(ms_path, true_demo,
                            num_loci=num_runs, mut_rate=theta,
                            additional_ms_params="-r %f 1000" % theta)
    
    cmle_search_res = momi.composite_mle_search(seg_sites, demo_func, params, maxiter=1000, bounds=bounds, **kwargs)
    est_params = cmle_search_res.x

    cr = momi.ConfidenceRegion(est_params, demo_func, seg_sites, regime=method, **kwargs)
    cov = cr.godambe(inverse=True)
    #cov = godambe_scaled_inv(method, est_params, seg_sites, demo_func)

    cr.test(params,sims=100)
    cr.test([params,est_params],sims=100)
    #log_lik_ratio_p(method, 1000, est_params, params, [True] * len(params), seg_sites, demo_func)

def check_jointime_cov(method, num_runs, theta):
    t0 = random.uniform(.25,2.5)
    t1 = t0 + random.uniform(.5,5.0)
    def demo_func(t):
        return simple_three_pop_demo(t,t1)
    check_cov(method, [t0], demo_func, num_runs, theta)
    
def test_jointime_cov_many():
    check_jointime_cov("many", 1000, 1.)
    
def test_jointime_cov_long():
    check_jointime_cov("long", 10, 100.)

def check_admixture_cov(method, num_runs, theta):
    check_cov(method, simple_nea_admixture_demo.true_params, simple_nea_admixture_demo, num_runs, theta, bounds = simple_nea_admixture_demo.bounds)

def test_admixture_cov_many():
    check_admixture_cov("many", 1000, 1.)

def test_admixture_cov_long():
    check_admixture_cov("long", 10, 100.)    