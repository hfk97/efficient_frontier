import math

# needed for the next function
import subprocess
import importlib
import sys


# function that imports a library if it is installed, else installs it and then imports it
def getpack(package):
    try:
        return importlib.import_module(package)
    except ImportError:
        subprocess.call([sys.executable, "-m", "pip", "install", package],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return importlib.import_module(package)


scipy = getpack("scipy")
np = getpack("numpy")

from scipy import optimize as opt


class Portfolio:
    def __init__(self, weights, std, mu, sr):
        self.weights = weights
        self.std = std
        self.mu = mu
        self.sr = sr


def sigma_p(weights, cov_matr):
    return math.sqrt(np.matmul(weights.transpose(), np.matmul(cov_matr, weights)))


def mu_check(weights, mus, mu_target):
    return mu_target-sum([weights[i]*mus[i] for i in range(len(weights))])


def optimal_portfolio(mus, cov_matrix, mu_target, rf, option=0):
    n = len(mus)

    # constraints
    # sum of all weights must be zero and portfolio mu must be target mu
    cons = [{'type': 'eq', 'fun': lambda x: 1 - sum(x)}, {'type': 'eq', 'fun': mu_check, 'args': (mus, mu_target)}]

    # without short-selling
    if option == 0:
        # Required to have non negative values
        bnds = tuple((0, 1) for x in range(n))

    # with short-selling
    elif option == 1:
        # Required to have non negative values
        bnds = tuple((-1, 1) for x in range(n))

    else:
        print("Error invalid option")
        return

    res = opt.minimize(sigma_p, np.array([1.0/n] * n), method='SLSQP', args=cov_matrix, bounds=bnds, constraints=cons)
    port_ret = sum([a*b for a, b in zip(res.x, mus)])

    return Portfolio(res.x, res.fun, port_ret, (port_ret - rf) / res.fun)


def min_var_portfolio(mus, cov_matrix, rf):
    n = len(mus)
    inv_cov_matrix = np.linalg.inv(cov_matrix)
    sig = math.sqrt(1.0 / inv_cov_matrix.sum())
    weights = np.matmul(inv_cov_matrix, np.array([1]*n)) / sum(np.matmul(inv_cov_matrix, np.array([1]*n)))
    port_ret = sum([a*b for a, b in zip(weights, mus)])

    return Portfolio(weights, sig, port_ret, (port_ret - rf) / sig)


def tangency_portfolio(mus, cov_matrix, rf):
    alph = [i-rf for i in mus]
    inv_cov_matrix = np.linalg.inv(cov_matrix)

    weights = np.matmul(inv_cov_matrix, alph) / sum(np.matmul(inv_cov_matrix, alph))
    sig = sigma_p(weights, cov_matrix)
    port_ret = sum([a*b for a, b in zip(weights, mus)])

    return Portfolio(weights, sig, port_ret, (port_ret - rf) / sig)


def efficient_frontier(mus, cov_matrix, rf, r_range):
    efficients = []
    for ret in r_range:
        efficients.append(optimal_portfolio(mus, cov_matrix, ret, rf))
    return efficients
