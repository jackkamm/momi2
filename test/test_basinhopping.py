from demography import make_demography
from maximum_likelihood import LogLikelihoodPRF
from scipy.optimize import basinhopping, minimize
import autograd.numpy as np
from autograd.numpy import log,exp,dot
from autograd import grad, hessian_vector_product

from util import memoize, aggregate_sfs

def simple_human_demo(n,
                      #t_bottleneck_to_africa_split,
                      t_africa_split_to_eurasia_split,
                      t_eurasia_split_to_present,
                      #ancestral_size,
                      africa_size, eurasia_size,
                      eur_present_size, asia_present_size):
    demo_cmd = " ".join(["-I 3 %s" % (" ".join(map(str,n))),
                         "-n 1 $0", # present pop size of africa
                         "-n 2 $1", # present pop size of europe
                         "-n 3 $2", # present pop size of asia
                         "-ej $3 3 2 -en $3 2 $4", # eurasia merge and bottleneck
                         "-ej $5 2 1", # eurasia,africa merge
                         "-en $6 1 $7", # ancestral pop size
                         ])
    ancestral_size=africa_size
    t_bottleneck_to_africa_split=0.0

    eurasia_split = exp(t_eurasia_split_to_present)
    africa_split = eurasia_split + exp(t_africa_split_to_eurasia_split)
    bottleneck = africa_split + exp(t_bottleneck_to_africa_split)

    demo = make_demography(demo_cmd,
                           exp(africa_size),
                           exp(eur_present_size),
                           exp(asia_present_size),
                           eurasia_split, exp(eurasia_size),
                           africa_split,
                           bottleneck, exp(ancestral_size))
    return demo,None

def check_simple_human_demo():
    #n = [10] * 3
    n = [5] * 3
    #theta = 1.0
    num_sims = 10000
    #true_params = np.exp(np.random.normal(size=6))
    true_params = np.random.normal(size=6)
    
    demo_func = lambda x: simple_human_demo(n, *x)
    true_demo,_ = demo_func(true_params)
    #true_demo = simple_human_demo(n, *true_params)

    p = len(true_params)
    true_x = true_params[:p]
    #init_x = np.exp(np.random.normal(size=p))
    init_x = np.random.normal(size=p)

    #sfs,_,_ = true_demo.simulate_sfs(num_sims, theta)
    #sfs,_,_ = true_demo.simulate_sfs(num_sims)
    #sfs = aggregate_sfs(true_demo.simulate_sfs(num_sims))
    sfs_list = true_demo.simulate_sfs(num_sims)

    log_lik_prf = LogLikelihoodPRF(demo_func, sfs_list)

    def objective(x):
        print (np.asarray(x) - true_x) / true_x
        return objective_helper(tuple(np.ravel(x)))

    def objective_helper(x):
        x = np.ravel(x)
        #print x
        #print (np.asarray(x) - true_x) / true_x
        params = list(true_params)
        #x = map(adnumber,x)

        params[:p] = x
        #ret = -log_likelihood_prf(simple_human_demo(n, *params), theta * num_sims, sfs)
        ret = -log_lik_prf.log_likelihood(params)
        return ret
        #return np.asarray(ret)
        #return np.asarray(ret.x), np.asarray(ret.gradient(x)), np.asarray(ret.hessian(x))

    f = objective
    g = grad(objective_helper)
    #gdot = lambda x,y: dot(y, g(x))
    #hp = grad(gdot)
    #hp = lambda x,vector: hessian_vector_product(objective_helper, argnum=0)(vector,x)
    hp = hessian_vector_product(objective_helper, argnum=0)
#     f = lambda x: objective(x)[0]
#     g = lambda x: objective(x)[1]
#     h = lambda x: objective(x)[2]


    #true_lik = objective(true_x)
    #print "\n".join(map(str,true_lik))
    print f(true_x),"\n",g(true_x)

    print true_x, "\n",init_x

    def accept_test(x_new,**kwargs):
        return bool(np.all(x_new > 1e-6))

    def print_fun(x, f, accepted):
        print x
        print("at minimum %.4f accepted %d" % (f, int(accepted)))

    #inferred_x = basinhopping(f, init_x, minimizer_kwargs = {'jac':g,'hess':h,'method':'trust-ncg'}, niter=10, callback=print_fun)
    #inferred_x = minimize(f, init_x, jac=g,hess=h,method='newton-cg')
    inferred_x = minimize(f, init_x, jac=g,hessp=hp,method='newton-cg')

    print inferred_x
    error = max(abs((true_x - inferred_x.x) / true_x))
    print true_x, "\n", inferred_x.x
    print error
    assert error < .05

if __name__ == "__main__":
    #set_order(2)
    check_simple_human_demo()
