from __future__ import division
import pytest
from ad import gh, adnumber
from admath import exp,log
import numpy as np
from size_history import ConstantTruncatedSizeHistory, PiecewiseHistory
import networkx as nx
from demography import Demography, normalizing_constant
import random
from sum_product import SumProduct
import math
from numdifftools import Gradient, Hessian

EPS=1e-8

def num_grad(f,x,eps=EPS):
    ret = []
    for i in range(len(x)):
        dx = np.zeros(len(x))
        dx[i] = eps
        ret.append((f(x+dx) - f(x)) / eps)
    return np.array(ret)

# this is numerically unstable
def num_hess(f,x,eps=EPS):
    def g(y):
        return num_grad(f,y,eps)
    return num_grad(g,x,math.sqrt(eps))
    #return num_grad(g,x,eps)

def log_within(x, y, eps=1e-2, trunc=1e-12):
    approx_zero = np.logical_or(np.abs(x) < trunc, np.abs(y) < trunc)
    not_zero = np.logical_not(approx_zero)
    if np.any(not_zero):
        assert max(np.abs(np.log(x[not_zero] / y[not_zero]))) < eps
    if np.any(approx_zero):
        assert np.max(np.abs(x[approx_zero])) < trunc and np.max(np.abs(y[approx_zero])) < trunc

def check_gradient(f, x):
    xd = np.asarray(adnumber(x))
    fxd = f(xd)
    grad1 = np.asarray(fxd.gradient(xd))

    #grad2 = num_grad(f, x)
    grad2 = Gradient(f)(x)

    print x, "\n", f(x)

    print "gradient1\n", grad1, "\ngradient2\n", grad2
    log_within(grad1,grad2)

    # note: numerical hessian can be numerically unstable!
#     hess1 = np.asarray(map(np.asarray, fxd.hessian(xd)))
# #     hess2 = num_hess(f,x)
#     hess2 = Hessian(f)(x)

#     print "hessian1\n", hess1,"\nhessian2\n",hess2,"\nhessian_diff\n", hess1-hess2
#     log_within(hess1,hess2,trunc=1e-7)

def test_simple():
    def f(x):
        return np.sum(np.outer(x,x))
    check_gradient(f, np.random.normal(size=10))

def test_simple_2():
    def f(x):
        return np.sum(1.0 / np.outer(x,x))
    check_gradient(f, np.random.normal(size=10))

def test_simple_3():
    def f(x):
        #return sum(x/x)
        return sum(x) / sum(x)
    check_gradient(f, np.random.normal(size=10))

def simple_two_pop_demo(x, n_lins):
    assert len(x) == 4
    assert list(sorted(n_lins.keys())) == ['a','b']

    demo = nx.DiGraph([('ab','a'), ('ab','b')])
    nd = dict(demo.nodes(data=True))
    nd['a']['lineages'] = n_lins['a']
    nd['b']['lineages'] = n_lins['b']
    
    demo = Demography(demo)
    nd = demo.node_data
    nd['a']['model'] = ConstantTruncatedSizeHistory(N=exp(x[1]), tau=exp(x[0]), n_max = n_lins['a'])
    nd['b']['model'] = ConstantTruncatedSizeHistory(N=exp(x[2]), tau=exp(x[0]), n_max = n_lins['b'])
    nd['ab']['model'] = ConstantTruncatedSizeHistory(N=exp(x[3]), tau=float('inf'),
                                                     n_max = n_lins['a'] + n_lins['b'])
    return demo

def piecewise_constant_demo(x, n_lins):
    assert len(x) % 2 == 1
    assert n_lins.keys() == ['a']
    n = n_lins['a']

    pieces = []
    for i in range(int((len(x)-1)/2)):
        pieces.append(ConstantTruncatedSizeHistory(n, exp(x[2*i]), exp(x[2*i+1])))
    pieces.append(ConstantTruncatedSizeHistory(n, float('inf'), exp(x[-1])))
    sizes = PiecewiseHistory(pieces)

    demo = nx.DiGraph([])
    demo.add_node('a')
    nd = dict(demo.nodes(data=True))
    nd['a']['lineages'] = n_lins['a']
    demo = Demography(demo)
    nd = demo.node_data['a']
    nd['model'] = sizes

    return demo


def sfs_func(demo_func, n_lins, normalized=True):
    # get random sfs entry
    n = sum([x for _,x in n_lins.items()])
    total_der = 0
    while total_der == 0 or total_der == n:
        total_der = 0
        states = {}
        for pop,n_pop in n_lins.items():
            n_der = random.randint(0,n_pop)
            assert n_der >= 0 and n_der <= n_pop
            total_der += n_der
            states[pop] = {'ancestral' : n_pop - n_der, 'derived' : n_der}
    
    print states
    def f(x):
        demo = demo_func(x, n_lins)
        demo.update_state(states)
        #return SumProduct(demo).p(normalized=normalized)
        ret = SumProduct(demo).p(normalized=False)
        if normalized:
            ret = ret / demo.totalSfsSum
            #ret = log(ret) - log(demo.totalSfsSum)
        return ret
    return f

@pytest.mark.parametrize("n,epochs,normalized", 
                         ((random.randint(2,10),random.randint(1,10),norm) for norm in (False,True)))
def test_piecewise_constant_p(n, epochs, normalized):
    n_lins = {'a' : n}

    x = np.random.normal(size=2*epochs - 1)
    #x = np.zeros(2*epochs-1)
    f = sfs_func(piecewise_constant_demo, n_lins, normalized=normalized)

    check_gradient(f,x)


# def normalizing_constant_func(demo_func, n_lins):
#     def f(x):
#         demo = demo_func(x, n_lins)
#         return demo.totalSfsSum
#     return f
# @pytest.mark.parametrize("n,epochs", 
#                          ((5,5),))
# def test_piecewise_constant_normalizing(n, epochs):
#     n_lins = {'a' : n}

#     x = np.random.normal(size=2*epochs - 1)
#     f = normalizing_constant_func(piecewise_constant_demo, n_lins)

#     check_gradient(f,x)

@pytest.mark.parametrize("n1,n2,normalized", 
                         ((random.randint(1,10),random.randint(1,10),norm) for norm in (False,True)))
def test_simple_two_pop(n1,n2,normalized):
    n_lins = {'a' : n1, 'b' : n2}

    x = np.random.normal(size=4)
    f = sfs_func(simple_two_pop_demo, n_lins, normalized=normalized)
    
    check_gradient(f,x)


def simple_five_pop_demo(x, epochs_per_pop, n_lins):
    # number of edges is 2n-1
    total_epochs = epochs_per_pop * (2*len(n_lins)-1)
    assert len(x) == 2 * total_epochs + 1 # a size and a time for each epoch, plus a final size
    assert list(sorted(n_lins.keys())) == ['a','b','c','d','e']

    demo = nx.DiGraph([('ab','a'), ('ab','b'),
                       ('cd','c'), ('cd','d'),
                       ('cde','cd'), ('cde','e'),
                       ('abcde','ab'),('abcde','cde')])
    nd = dict(demo.nodes(data=True))
    for v in ('a','b','c','d','e'):
        nd[v]['lineages'] = n_lins[v]
        nd[v]['lineages'] = n_lins[v]
    
    demo = Demography(demo)
    nd = demo.node_data
    pops = sorted(nd.keys())
    i = 0
    for v in pops:
        pieces = []
        for j in range(epochs_per_pop):
            pieces.append(ConstantTruncatedSizeHistory(N=exp(x[i]), tau=exp(x[i+1]), n_max = demo.n_lineages_subtended_by[v]))
            i += 2
        if v == 'abcde':
            pieces.append(ConstantTruncatedSizeHistory(N=exp(x[i]), tau=float('inf'), n_max = demo.n_lineages_subtended_by[v]))
            i += 1
        nd[v]['model'] = PiecewiseHistory(pieces)
    return demo


@pytest.mark.parametrize("n1,n2,n3,n4,n5,e,normalized", 
                         ((random.randint(1,5),random.randint(1,5),random.randint(1,5),random.randint(1,5),random.randint(1,5),3,norm) for norm in (False,True)))
def test_simple_five_pop(n1,n2,n3,n4,n5,e,normalized):
    n_lins = {'a' : n1, 'b' : n2, 'c' : n3, 'd' : n4, 'e' : n5}

    epochs_per_pop=e
    total_epochs = epochs_per_pop * (2*len(n_lins)-1)
    x_len = 2 * total_epochs + 1 # a size and a time for each epoch, plus a final size

    x = np.random.normal(size=x_len)
    def demo_func(y,n_lins):
        return simple_five_pop_demo(y,epochs_per_pop,n_lins)
    f = sfs_func(demo_func, n_lins, normalized=normalized)
    
    check_gradient(f,x)
